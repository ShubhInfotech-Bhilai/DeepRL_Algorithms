#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created at 2020/1/2 下午10:30
import pickle

import torch
import torch.optim as optim

from Algorithms.pytorch.Models.Policy import Policy
from Algorithms.pytorch.Models.Policy_discontinuous import DiscretePolicy
from Algorithms.pytorch.Models.Value import Value
from Algorithms.pytorch.VPG.vpg_step import vpg_step
from Common.GAE import estimate_advantages
from Common.MemoryCollector import MemoryCollector
from Utils.env_util import get_env_info
from Utils.file_util import check_path
from Utils.torch_util import DOUBLE, device
from Utils.zfilter import ZFilter


class VPG:
    def __init__(self,
                 env_id,
                 render=False,
                 num_process=1,
                 min_batch_size=2048,
                 lr_p=3e-4,
                 lr_v=1e-3,
                 gamma=0.99,
                 tau=0.95,
                 vpg_epochs=10,
                 seed=1,
                 model_path=None
                 ):
        self.env_id = env_id
        self.gamma = gamma
        self.tau = tau
        self.render = render
        self.num_process = num_process
        self.lr_p = lr_p
        self.lr_v = lr_v
        self.min_batch_size = min_batch_size
        self.vpg_epochs = vpg_epochs
        self.model_path = model_path
        self.seed = seed

        self._init_model()

    def _init_model(self):
        """init model from parameters"""
        self.env, env_continuous, num_states, num_actions = get_env_info(self.env_id)

        # seeding
        torch.manual_seed(self.seed)
        self.env.seed(self.seed)

        if env_continuous:
            self.policy_net = Policy(num_states, num_actions).double().to(device)  # current policy
        else:
            self.policy_net = DiscretePolicy(num_states, num_actions).double().to(device)

        self.value_net = Value(num_states).double().to(device)
        self.running_state = ZFilter((num_states,), clip=5)

        if self.model_path:
            print("Loading Saved Model {}_vpg.p".format(self.env_id))
            self.policy_net, self.value_net, self.running_state = pickle.load(
                open('{}/{}_vpg.p'.format(self.model_path, self.env_id), "rb"))

        self.collector = MemoryCollector(self.env, self.policy_net, render=self.render,
                                         running_state=self.running_state,
                                         num_process=self.num_process)

        self.optimizer_p = optim.Adam(self.policy_net.parameters(), lr=self.lr_p)
        self.optimizer_v = optim.Adam(self.value_net.parameters(), lr=self.lr_v)

    def choose_action(self, state):
        """select action"""
        state = DOUBLE(state).unsqueeze(0).to(device)
        with torch.no_grad():
            action, log_prob = self.policy_net.get_action_log_prob(state)
        return action, log_prob

    def eval(self, i_iter):
        """init model from parameters"""
        state = self.env.reset()
        test_reward = 0
        while True:
            self.env.render()
            state = self.running_state(state)

            action, _ = self.choose_action(state)
            action = action.cpu().numpy()[0]
            state, reward, done, _ = self.env.step(action)

            test_reward += reward
            if done:
                break
        print(f"Iter: {i_iter}, test Reward: {test_reward}")
        self.env.close()

    def learn(self, writer, i_iter):
        """learn model"""
        memory, log = self.collector.collect_samples(self.min_batch_size)

        print(f"Iter: {i_iter}, num steps: {log['num_steps']}, total reward: {log['total_reward']: .4f}, "
              f"min reward: {log['min_episode_reward']: .4f}, max reward: {log['max_episode_reward']: .4f}, "
              f"average reward: {log['avg_reward']: .4f}, sample time: {log['sample_time']: .4f}")

        # record reward information
        writer.add_scalars("vpg",
                           {"total reward": log['total_reward'],
                            "average reward": log['avg_reward'],
                            "min reward": log['min_episode_reward'],
                            "max reward": log['max_episode_reward'],
                            "num steps": log['num_steps']
                            }, i_iter)

        batch = memory.sample()  # sample all items in memory

        batch_state = DOUBLE(batch.state).to(device)
        batch_action = DOUBLE(batch.action).to(device)
        batch_reward = DOUBLE(batch.reward).to(device)
        batch_mask = DOUBLE(batch.mask).to(device)

        with torch.no_grad():
            batch_value = self.value_net(batch_state)

        batch_advantage, batch_return = estimate_advantages(batch_reward, batch_mask, batch_value, self.gamma,
                                                            self.tau)
        v_loss, p_loss = vpg_step(self.policy_net, self.value_net, self.optimizer_p, self.optimizer_v, self.vpg_epochs,
                                  batch_state,
                                  batch_action, batch_return, batch_advantage,
                                  1e-3)
        return v_loss, p_loss

    def save(self, save_path):
        """save model"""
        check_path(save_path)
        pickle.dump((self.policy_net, self.value_net, self.running_state),
                    open('{}/{}_vpg.p'.format(save_path, self.env_id), 'wb'))
