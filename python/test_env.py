from env.battle_env import BattleEnv

env = BattleEnv()
obs, info = env.reset()
print(f"Initial state: {obs}")

# take one random action
action = 3  # use move 1
obs, reward, terminated, truncated, info = env.step(action)
print(f"After action: {obs}")
print(f"Reward: {reward}")
print(f"Battle over: {terminated}")