from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import StopTrainingOnMaxEpisodes
from env.battle_env import BattleEnv

env = BattleEnv()
model = PPO("MlpPolicy", env, verbose=1, ent_coef=0.1, n_steps=128)

# Stop after 50 battles (one episode = one full Brock fight).
# total_timesteps is set very high so the callback is what actually
# ends training, not the step budget.
stop_callback = StopTrainingOnMaxEpisodes(max_episodes=50, verbose=1)
model.learn(total_timesteps=10_000_000, callback=stop_callback)

model.save("brock_ppo")
print("Training done!")