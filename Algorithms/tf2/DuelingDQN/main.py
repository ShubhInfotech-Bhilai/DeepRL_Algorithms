#!/usr/bin/env python
# Created at 2020/3/22

import click

import tensorflow as tf

from Algorithms.tf2.DuelingDQN.duelingdqn import DuelingDQN


@click.command()
@click.option("--env_id", type=str, default="MountainCar-v0", help="Environment Id")
@click.option("--render", type=bool, default=False, help="Render environment or not")
@click.option("--num_process", type=int, default=1, help="Number of process to run environment")
@click.option("--lr", type=float, default=1e-3, help="Learning rate for Policy Net")
@click.option("--gamma", type=float, default=0.99, help="Discount factor")
@click.option("--epsilon", type=float, default=0.90, help="Probability controls greedy action")
@click.option("--explore_size", type=int, default=5000, help="Explore steps before execute deterministic policy")
@click.option("--memory_size", type=int, default=100000, help="Size of replay memory")
@click.option("--step_per_iter", type=int, default=1000, help="Number of steps of interaction in each iteration")
@click.option("--batch_size", type=int, default=128, help="Batch size")
@click.option("--min_update_step", type=int, default=1000, help="Minimum interacts for updating")
@click.option("--update_target_gap", type=int, default=50, help="Steps between updating target q net")
@click.option("--max_iter", type=int, default=500, help="Maximum iterations to run")
@click.option("--eval_iter", type=int, default=50, help="Iterations to evaluate the model")
@click.option("--save_iter", type=int, default=50, help="Iterations to save the model")
@click.option("--model_path", type=str, default="trained_models", help="Directory to store model")
@click.option("--log_path", type=str, default="../log/", help="Directory to save logs")
@click.option("--seed", type=int, default=1, help="Seed for reproducing")
def main(env_id, render, num_process, lr, gamma, epsilon, explore_size, memory_size, step_per_iter, batch_size,
         min_update_step, update_target_gap, max_iter, eval_iter, save_iter, model_path, log_path, seed):
    base_dir = log_path + env_id + "/DuelingDQN_exp{}".format(seed)
    writer = tf.summary.create_file_writer(base_dir)
    duelingdqn = DuelingDQN(env_id,
                            render=render,
                            num_process=num_process,
                            memory_size=memory_size,
                            lr_q=lr,
                            gamma=gamma,
                            epsilon=epsilon,
                            explore_size=explore_size,
                            step_per_iter=step_per_iter,
                            batch_size=batch_size,
                            min_update_step=min_update_step,
                            update_target_gap=update_target_gap,
                            seed=seed)

    for i_iter in range(1, max_iter + 1):
        duelingdqn.learn(writer, i_iter)

        if i_iter % eval_iter == 0:
            duelingdqn.eval(i_iter)

        if i_iter % save_iter == 0:
            duelingdqn.save(model_path)


if __name__ == '__main__':
    main()
