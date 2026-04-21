import gymnasium as gym
import numpy as np
import time
import ollama
from PIL import Image

from fire_red import get_battle_state, press_button, send_cmd

# Region of the screenshot containing the FIGHT/BAG/POKEMON/RUN menu box.
# GBA native resolution is 240x160; mGBA screenshots are typically saved at
# that size. The main battle menu sits in the bottom-right quadrant.
# (left, top, right, bottom) in pixels.
_MENU_CROP_BOX = (120, 96, 240, 160)
_MENU_MATCH_THRESHOLD = 12.0  # mean abs pixel diff; tweak if false positives

class BattleEnv(gym.Env):
    
    def __init__(self):
        super().__init__()
        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=(4,), dtype=np.float32
        )
        self.last_enemy_max_hp = None
        self._menu_reference = None  # cached crop of main battle menu

    def _grab_menu_crop(self):
        send_cmd("core.screenshot,/tmp/battle_screen.png")
        img = Image.open("/tmp/battle_screen.png").convert("RGB")
        # Some bridges save at 2x/3x native res; normalize to 240x160 first.
        if img.size != (240, 160):
            img = img.resize((240, 160), Image.BILINEAR)
        return np.asarray(img.crop(_MENU_CROP_BOX), dtype=np.int16)

    def reset(self, seed=None):
        send_cmd("core.loadStateFile,/Users/hrishishah/MLEngineer/pokegym/fight_save_slot.ss0,2")
        time.sleep(3)
        # Save state was taken on the main battle menu, so grab a reference
        # crop now to use for fast template matching later.
        self._menu_reference = self._grab_menu_crop()
        state = get_battle_state()
        self.last_enemy_max_hp = state["enemy_max_hp"]
        obs = np.array([
            state["my_hp"],
            state["my_max_hp"],
            state["enemy_hp"],
            state["enemy_max_hp"]
        ], dtype=np.float32)
        return obs, {}

    def step(self, action):
        if not self.in_fight_checker():
            # send_cmd("core.loadStateFile,/Users/hrishishah/MLEngineer/pokegym/fight_save_slot.ss0,2")
            time.sleep(5)
        
        before = get_battle_state()

        self.wait_for_turn()

        # Memory flag 0x02023BE3 also reads 0 between dialogue screens (e.g.
        # right after a faint, before the next mon's send-in message), so we
        # confirm we're truly on the FIGHT/BAG/POKEMON/RUN menu before
        # committing any directional inputs. Fast pixel match first, llava
        # only as a fallback. If not on the menu, press B to back out of
        # whatever menu we drifted into and skip this step as a no-op.
        if not self.is_main_battle_menu_fast():
            for _ in range(4):
                press_button("B")
                time.sleep(1.0)
            obs = np.array([
                before["my_hp"], before["my_max_hp"],
                before["enemy_hp"], before["enemy_max_hp"]
            ], dtype=np.float32)
            return obs, 0.0, False, False, {}

        press_button("A")  # open FIGHT submenu
        time.sleep(2.5)
        # Reset move cursor to top-left (slot 0) so action IDs map to fixed moves
        press_button("Left")
        time.sleep(0.3)
        press_button("Left")
        time.sleep(0.3)
        press_button("Up")
        time.sleep(0.3)
        press_button("Up")
        time.sleep(0.3)
        if action == 0:
            press_button("A")
        elif action == 1:
            press_button("Right")
            time.sleep(0.5)
            press_button("A")
        elif action == 2:
            press_button("Down")
            time.sleep(0.5)
            press_button("A")
        elif action == 3:
            press_button("Down")
            time.sleep(0.5)
            press_button("Right")
            time.sleep(0.5)
            press_button("A")
        
        # Let the move dialogue/animation actually resolve. wait_for_turn
        # mashes B through "X used Y!", damage animation, faint dialogue, etc.
        # until either the next turn menu appears (enemy alive or switched)
        # or it times out (battle is over and post-battle dialogue started).
        time.sleep(2)
        turn_came_back = self.wait_for_turn()
        after = get_battle_state()

        # track if new pokemon switched in
        if after["enemy_max_hp"] != before["enemy_max_hp"]:
            self.last_enemy_max_hp = after["enemy_max_hp"]

        if after["enemy_hp"] > before["enemy_hp"]:
            damage_dealt = before["enemy_hp"]
        else:
            damage_dealt = before["enemy_hp"] - after["enemy_hp"]
        
        damage_taken = before["my_hp"] - after["my_hp"]
        reward = damage_dealt - damage_taken

        # Battle-ended detection: wait_for_turn timed out = player never got
        # another turn = battle is truly over (we won, whiteout, trainer
        # ended the fight, etc.). This is the reliable signal. We intentionally
        # DON'T check is_main_battle_menu_fast here because during a mid-battle
        # switch-in (Geodude -> Onix) the menu briefly isn't drawn yet even
        # though the battle is still going, and that caused false terminations.
        battle_ended = not turn_came_back

        # only terminate when current enemy hp is 0 and no new pokemon switched in
        new_pokemon_switched = after["enemy_max_hp"] != before["enemy_max_hp"]

        # battle only ends if enemy hp is 0 AND no new pokemon came in
        enemy_all_fainted = after["enemy_hp"] == 0 and not new_pokemon_switched

        terminated = battle_ended or enemy_all_fainted or after["my_hp"] <= 0

        if terminated and after["enemy_hp"] <= 0:
            reward += 100
        if after["my_hp"] <= 0:
            reward -= 100

        if terminated:
            time.sleep(3)
            send_cmd("core.loadStateFile,/Users/hrishishah/MLEngineer/pokegym/fight_save_slot.ss0,2")
            time.sleep(3)

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
    
    def wait_for_turn(self):
        # Require the turn flag to read 0 for several consecutive checks so we
        # don't catch a flicker during fainting/switch-in dialogue. Press B
        # slowly so we don't mash through a menu that's briefly on-screen.
        stable_zero = 0
        for _ in range(40):
            val = int(send_cmd("core.read8,0x02023BE3"))
            if val == 0:
                stable_zero += 1
                if stable_zero >= 3:
                    return True
                time.sleep(0.3)
                continue
            stable_zero = 0
            press_button("B")  # advance dialogue
            time.sleep(1.0)    # slower: let the game actually process each B
        return False

    def is_main_battle_menu_fast(self):
        """Millisecond pixel-diff check against the reference menu captured in
        reset(). Falls back to the llava check if no reference is available
        yet (e.g. step() called before reset(), shouldn't happen)."""
        if self._menu_reference is None:
            return self.is_main_battle_menu()
        try:
            crop = self._grab_menu_crop()
        except Exception:
            return self.is_main_battle_menu()
        diff = np.abs(crop - self._menu_reference).mean()
        return diff < _MENU_MATCH_THRESHOLD

    def is_main_battle_menu(self):
        send_cmd("core.screenshot,/tmp/battle_screen.png")
        response = ollama.chat("llava", [{
            "role": "user",
            "content": (
                "Does this screen show the main Pokemon battle menu with the "
                "four options FIGHT, BAG, POKEMON, and RUN visible in a box? "
                "Reply with only YES or NO."
            ),
            "images": ["/tmp/battle_screen.png"]
        }])
        return "YES" in response.message.content.upper()

    def get_current_menu(self):
        send_cmd("core.screenshot,/tmp/battle_screen.png")
        response = ollama.chat("llava", [{
            "role": "user",
            "content": "Is this showing: A) the main battle menu with FIGHT/BAG/POKEMON/RUN, or B) the move selection menu with individual moves? Reply with only A or B.",
            "images": ["/tmp/battle_screen.png"]
        }])
        return response.message.content.strip()

    def in_fight_checker(self):
        send_cmd("core.screenshot,/tmp/battle_screen.png")
        response = ollama.chat("llava", [{
            "role": "user",
            "content": "Does this screen show a pokemon fight? Reply with only YES or NO.",
            "images": ["/tmp/battle_screen.png"]
        }])
        if "YES" in response.message.content.upper():
            return True
        time.sleep(1)
        return False