#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created at 2020/1/3 下午4:40

import click

from Algorithms.pytorch.PPO.ppo import PPO
from Algorithms.pytorch.PPO.ppo_mini_batch import PPO_Minibatch


@click.command()
@click.option("--env_id", type=str, default="Hopper-v2", help="Environment Id")
@click.option("--render", type=bool, default=False, help="Render environment or not")
@click.option("--num_process", type=int, default=4, help="Number of process to run environment")
@click.option("--lr_p", type=float, default=3e-4, help="Learning rate for Policy Net")
@click.option("--lr_v", type=float, default=3e-4, help="Learning rate for Value Net")
@click.option("--gamma", type=float, default=0.99, help="Discount factor")
@click.option("--tau", type=float, default=0.95, help="GAE factor")
@click.option("--epsilon", type=float, default=0.2, help="Clip rate for PPO")
@click.option("--batch_size", type=int, default=2048, help="Batch size")
@click.option("--mini_batch", type=bool, default=False, help="Update by mini-batch strategy")
@click.option("--ppo_mini_batch_size", type=int, default=64, help="PPO mini-batch size")
@click.option("--ppo_epochs", type=int, default=10, help="PPO step")
@click.option("--model_path", type=str, default="trained_models", help="Directory to store model")
@click.option("--seed", type=int, default=1, help="Seed for reproducing")
@click.option("--test_epochs", type=int, default=50, help="Trials to test model")
def main(env_id, render, num_process, lr_p, lr_v, gamma, tau, epsilon, batch_size, mini_batch,
         ppo_mini_batch_size, ppo_epochs, model_path, seed, test_epochs):
    if mini_batch:
        ppo = PPO_Minibatch(env_id, render, num_process, batch_size, lr_p, lr_v, gamma, tau, epsilon,
                            ppo_mini_batch_size,
                            ppo_epochs, seed=seed, model_path=model_path)
    else:
        ppo = PPO(env_id, render, num_process, batch_size, lr_p, lr_v, gamma, tau, epsilon,
                  ppo_epochs, seed=seed, model_path=model_path)

    for i_iter in range(1, test_epochs):
        ppo.eval(i_iter)


if __name__ == '__main__':
    main()
