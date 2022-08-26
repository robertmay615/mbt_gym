import gym
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import seaborn as sns

from DRL4AMM.agents.Agent import Agent
from DRL4AMM.gym.helpers.generate_trajectory import generate_trajectory


def plot_trajectory(env: gym.Env, agent: Agent, seed: int = None):
    # assert env.num_trajectories == 1, "Plotting a trajectory can only be done when env.num_trajectories == 1."
    timestamps = get_timestamps(env)
    observations, actions, rewards = generate_trajectory(env, agent, seed)
    cum_rewards = np.cumsum(rewards, axis=2)
    cash_holdings = observations[:, 0, :]
    inventory = observations[:, 1, :]
    asset_prices = observations[:, 3, :]
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 10))
    ax3a = ax3.twinx()
    ax1.title.set_text("cum_rewards")
    ax2.title.set_text("asset_prices")
    ax3.title.set_text("inventory and cash holdings")
    ax4.title.set_text("quoted spreads")
    for i in range(env.num_trajectories):
        ax1.plot(timestamps[1:], cum_rewards[i, 0, :])
        ax2.plot(timestamps, asset_prices[i, :])
        ax3.plot(
            timestamps, inventory[i, :], label=f"inventory {i}", color="r", alpha=(i + 1) / (env.num_trajectories + 1)
        )
        ax3a.plot(
            timestamps,
            cash_holdings[i, :],
            label=f"cash holdings {i}",
            color="b",
            alpha=(i + 1) / (env.num_trajectories + 1),
        )
        ax4.plot(
            timestamps[0:-1],
            actions[i, 0, :],
            label=f"bid half spread {i}",
            color="r",
            alpha=(i + 1) / (env.num_trajectories + 1),
        )
        ax4.plot(
            timestamps[0:-1],
            actions[i, 1, :],
            label=f"ask half spread {i}",
            color="b",
            alpha=(i + 1) / (env.num_trajectories + 1),
        )
    ax3.legend()
    ax4.legend()
    plt.show()


def plot_stable_baselines_actions(model, env):
    timestamps = get_timestamps(env)
    inventory_action_dict = {}
    price = 100
    cash = 100
    for inventory in [-3, -2, -1, 0, 1, 2, 3]:
        actions = model.predict([price, cash, inventory, 0], deterministic=True)[0].reshape((1, 2))
        for ts in timestamps[1:]:
            actions = np.append(
                actions, model.predict([price, cash, inventory, ts], deterministic=True)[0].reshape((1, 2)), axis=0
            )
        inventory_action_dict[inventory] = actions
    for inventory in [-3, -2, -1, 0, 1, 2, 3]:
        plt.plot(np.array(inventory_action_dict[inventory]).T[0], label=inventory)
    plt.legend()
    plt.show()
    for inventory in [-3, -2, -1, 0, 1, 2, 3]:
        plt.plot(np.array(inventory_action_dict[inventory]).T[1], label=inventory)
    plt.legend()
    plt.show()


def plot_pnl(rewards, symmetric_rewards=None):
    fig, ax = plt.subplots(1, 1, figsize=(20, 10))
    if symmetric_rewards is not None:
        sns.histplot(symmetric_rewards, label="Rewards of symmetric strategy", stat="density", bins=50, ax=ax)
    sns.histplot(rewards, label="Rewards", color="red", stat="density", bins=50, ax=ax)
    ax.legend()
    plt.close()
    return fig


def generate_results_table_and_hist(env: gym.Env, agent: Agent, n_episodes: int = 1000):
    half_spreads = []
    total_as_rewards = []
    as_terminal_inventories = []
    for _ in range(n_episodes):
        observations, actions, rewards = generate_trajectory(env, agent)
        total_as_rewards.append(sum(rewards))
        as_terminal_inventories.append(observations[-1][2])
        half_spread = np.array(actions).mean()
        half_spreads.append(half_spread)

    rows = ["Inventory"]
    columns = ["Mean spread", "Mean PnL", "Std PnL", "Mean terminal inventory", "Std terminal inventory"]
    results = pd.DataFrame(index=rows, columns=columns)
    results.loc[:, "Mean spread"] = 2 * np.mean(half_spreads)
    results.loc["Inventory", "Mean PnL"] = np.mean(total_as_rewards)
    results.loc["Inventory", "Std PnL"] = np.std(total_as_rewards)
    results.loc["Inventory", "Mean terminal inventory"] = np.mean(as_terminal_inventories)
    results.loc["Inventory", "Std terminal inventory"] = np.std(as_terminal_inventories)

    fig = plot_pnl(total_as_rewards)

    return results, fig, total_as_rewards


def get_timestamps(env):
    return np.linspace(0, env.terminal_time, env.n_steps + 1)
