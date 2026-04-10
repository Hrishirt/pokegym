import gymnasium as gym
import numpy as np
import time
from fire_red import get_battle_state, press_button, send_cmd
class BattleEnv(gym.Env):
    
    def __init__(self):
        super().__init__()
        # 4 moves to choose from
        self.action_space = gym.spaces.Discrete(4)
        # state vector: [my_hp, my_max_hp, enemy_hp, enemy_max_hp]
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=(4,), dtype=np.float32
        )

    def reset(self, seed=None):
        send_cmd("core.loadStateSlot,2")
        time.sleep(3) 
        state = get_battle_state()
        obs = np.array([
            state["my_hp"],
            state["my_max_hp"],
            state["enemy_hp"],
            state["enemy_max_hp"]
        ], dtype=np.float32)
        return obs, {}

    def step(self, action):
        # press the right button for the action
        # read new state
        # calculate reward
        # check if done
        # return obs, reward, terminated, truncated, info
        before = get_battle_state()
        before_total = before["enemy_hp"] + before["my_hp"]
        if action == 0:
            press_button("A")  # select FIGHT
            time.sleep(0.5)
            press_button("A")  # select move 1
        elif action == 1:
            press_button("A")  # select FIGHT
            time.sleep(0.5)
            press_button("Down")
            press_button("A")  # select move 2
        elif action == 2:
            press_button("A")  # select FIGHT
            time.sleep(0.5)
            press_button("Right")
            press_button("A")  # select move 3
        elif action == 3:
            press_button("A")  # select FIGHT
            time.sleep(0.5)
            press_button("Down")
            press_button("Right")
            press_button("A")  # select move 4
        time.sleep(2)
        # read state AFTER action
        after = get_battle_state()
        if after["enemy_hp"] > before["enemy_hp"]:
            damage_dealt = before["enemy_hp"]  # dealt remaining HP to finish them
        else:
            damage_dealt = before["enemy_hp"] - after["enemy_hp"]
        
        damage_taken = before["my_hp"] - after["my_hp"]
        reward = damage_dealt - damage_taken
        terminated = after["enemy_hp"] <= 0 or after["my_hp"] <= 0
        if after["enemy_hp"] <= 0:
            reward += 100  # won
        if after["my_hp"] <= 0:
            reward -= 100  # lost
        
        # build observation
        obs = np.array([
            after["my_hp"],
            after["my_max_hp"],
            after["enemy_hp"],
            after["enemy_max_hp"]
        ], dtype=np.float32)
        
        return obs, reward, terminated, False, {}
    def render(self):
        state = get_battle_state()
        print(state)