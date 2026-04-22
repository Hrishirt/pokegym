# Pokegym

A reinforcement learning agent that autonomously plays Pokémon FireRed and beats Gym Leader Brock — with no hardcoded game knowledge, no type chart, and no human input during battle.

## What This Is

pokegym is a custom Gymnasium environment that wraps the mGBA GBA emulator via a TCP socket bridge, extracts live battle state directly from the game’s RAM, and trains a PPO agent to make turn-by-turn combat decisions. The agent learns purely from reward signals — it discovers that Water Gun is effective against Rock-type Pokémon on its own.

## Architecture

```
mGBA Emulator (Lua TCP Server)
        ↕  socket bridge
Python Client (fire_red.py)
        ↕  battle state
Custom Gymnasium Environment (BattleEnv)
        ↕  observations + rewards
PPO Agent (Stable Baselines3)
        ↕  actions (move selection)
Button Injection → mGBA
```

## The Hard Parts

Building this was significantly harder than just calling `PPO.learn()`. The real engineering challenges were:

**Memory extraction from a live GBA process**
FireRed stores Pokémon data in an encrypted 100-byte structure in RAM. The encryption key is derived from each Pokémon’s personality value, meaning you can’t read species or move data directly. HP and max HP are stored unencrypted at specific offsets — finding those offsets required cross-referencing the Data Crystal RAM map, Bulbapedia’s Generation III data structure documentation, and empirical scanning. The player party starts at `0x02024284` and the enemy party at `0x0202402C`, but getting to verified, working addresses took significant debugging.

**Dynamic pointer resolution**
Player position data in FireRed lives at a dynamic address — `[0x03005008] + offset` — because the save block is DMA-protected and moves around in memory. Reading position requires first reading the pointer at `0x03005008`, then offsetting from there. This is a two-read operation and the root cause of every early memory read returning garbage.

**TCP socket bridge between Lua and Python**
mGBA’s scripting API is Lua-only. Python can’t talk to the emulator directly. The solution was loading a Lua TCP server inside mGBA that listens on a local port and exposes memory read/write and button injection via a simple message protocol. Python connects as a client and sends commands like `core.read16,0x02024284`. Building this bridge was the foundational piece everything else depends on.

**Multi-Pokémon reward shaping**
Brock has two Pokémon — Geodude and Onix. When Geodude faints and Onix switches in, enemy HP goes from 0 to 33. A naive reward function reads this as the enemy healing and gives a large negative reward. The fix was detecting the switch by comparing `enemy_max_hp` before and after each turn — if max HP changes, a new Pokémon entered and the damage dealt was the remaining HP of the previous one, not the difference between frames.

**Turn detection without vision**
The agent needs to know when it’s actually its turn before pressing buttons — otherwise it fires inputs during enemy animations, dialogue boxes, or faint sequences and lands in wrong menus. The solution was a memory address at `0x02023BE3` that tracks battle turn state: `0` means the player’s turn, non-zero means the game is processing. Polling this address replaced an earlier LLaVA vision approach that was 2000x slower.

**State loading and episode resets**
PPO calls `reset()` between episodes, but the game doesn’t know that. After a battle ends the game plays victory animations, shows dialogue, and transitions to the overworld — all while the agent is still injecting button presses. The fix was saving a `.ss0` state file directly to disk via `core.loadStateFile` and loading it on every reset, combined with detecting battle end via HP state and stopping all input immediately on termination.

## State Space

Each observation is a 4-dimensional vector read directly from RAM:

|Index|Value            |Address                          |
|-----|-----------------|---------------------------------|
|0    |Player current HP|`0x02024284 + 0x56`              |
|1    |Player max HP    |`0x02024284 + 0x58`              |
|2    |Enemy current HP |`0x0202402C + 0x56` (active slot)|
|3    |Enemy max HP     |`0x0202402C + 0x58` (active slot)|

## Reward Function

```python
damage_dealt = before_enemy_hp - after_enemy_hp
damage_taken = before_my_hp - after_my_hp
reward = damage_dealt - damage_taken

if enemy_fainted:
    reward += 100
if player_fainted:
    reward -= 100
```

No type chart. No move database. The agent learns that Water Gun produces higher `damage_dealt` values against Brock’s team and converges toward it naturally.

## Stack

- Python 3.10+
- Stable Baselines3 — PPO implementation
- Gymnasium — environment interface
- mGBA — GBA emulator with Lua scripting API
- mGBA-http — Lua TCP server loaded into mGBA

## Setup

### Prerequisites

- mGBA 0.10+
- Python 3.10+
- A Pokemon FireRed ROM (US v1.0, game code BPRE) — not included

### Install dependencies

```bash
pip install gymnasium stable-baselines3 numpy
```

### Load the Lua server in mGBA

1. Open mGBA and load your FireRed ROM
1. Tools → Scripting → File → Load Script → select `lua/mGBASocketServer.lua`
1. Console should show: `mGBA script server ready. Listening on port 8888`

### Save your training state

Position your party in front of Brock with the battle menu showing, then save the state file to `fight_save_slot.ss0`.

### Train

```bash
cd python
python train.py
```

## Project Structure

```
pokegym/
├── lua/
│   └── mGBASocketServer.lua
├── python/
│   ├── fire_red.py
│   ├── env/
│   │   └── battle_env.py
│   ├── train.py
│   └── test_env.py
└── README.md
```

## Reflections

This project started as a portfolio piece and became a deep dive into systems programming, memory architecture, and the gap between RL theory and RL practice.

The ML part — PPO, reward functions, observation spaces — was the easy part to understand conceptually. The hard part was everything underneath it: why memory addresses return garbage until you resolve the pointer, why button presses fire out of order without careful timing, why a reward function that looks correct on paper produces nonsensical behavior in training.

Real RL is not CartPole. The environment is the project.

## What’s Next

A vision-based navigation agent that walks from Pallet Town to Pewter City autonomously — no waypoints, no scripted paths. The battle agent handles combat; the navigation agent handles everything else.
