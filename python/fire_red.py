import socket
s = socket.socket()
s.settimeout(5)
s.connect(('localhost', 8888))

def send_cmd(cmd):
    s.send((cmd + "<|END|>").encode())
    return s.recv(1024).decode().replace("<|END|>", "")

def get_player_state():
    ptr = int(send_cmd("core.read32,0x03005008"))
    x = int(send_cmd(f"core.read16,{ptr}"))
    y = int(send_cmd(f"core.read16,{ptr + 2}"))
    map_num = int(send_cmd(f"core.read8,{ptr + 4}"))
    map_bank = int(send_cmd(f"core.read8,{ptr + 5}"))
    return {"x": x, "y": y, "map_num": map_num, "map_bank": map_bank}

def press_button(btn):
    send_cmd(f"mgba-http.button.tap,{btn}")

def load_state_file(path):
    # 1. Use double quotes and ensure the path string is clean
    # 2. Some mGBA Lua bridges require you to escape the slashes
    # safe_path = path.replace("/", "\\/") 
    
    # Send the command using the Lua namespace
    # Many bridges require 'lua.' or 'emu.' prefixing
    # Try this variant
    send_cmd("core.loadStateFile,/Users/hrishishah/MLEngineer/pokegym/fight_save_slot.ss0,2")
# Movement testing 
'''
print(f"Player state before moving Right: {get_player_state()}")
press_button("Right")
print(f"Player state afer moving Right: {get_player_state()}")
'''
# print(get_player_state())
# send_cmd("core.screenshot,/Users/hrishishah/MLEngineer/pokegym/images/screen.png")
# print(f"Screenshot saved")
# send_cmd("core.write32,0x02024298,1000")
# print("level changed")

# Base memory address for pokemon party and then using memory offsets to find the hp and max hp of the pokemon. 
def get_battle_state():
    player_base = 0x02024284
    
    # Base address for the start of the enemy party 
    enemy_party_base = 0x0202402C
    
    my_hp = int(send_cmd(f"core.read16,{player_base + 0x56}"))
    my_max_hp = int(send_cmd(f"core.read16,{player_base + 0x58}"))
    
    # Read Geodude's HP first
    enemy_hp = int(send_cmd(f"core.read16,{enemy_party_base + 0x56}"))
    enemy_max_hp = int(send_cmd(f"core.read16,{enemy_party_base + 0x58}"))
    
    # If Geodude's HP is 0 he's fainted. Switch to tracking Onix.
    if enemy_hp == 0:
        onix_base = enemy_party_base + 0x64  # This equals your 0x02024090
        enemy_hp = int(send_cmd(f"core.read16,{onix_base + 0x56}"))
        enemy_max_hp = int(send_cmd(f"core.read16,{onix_base + 0x58}"))

    return {
        "my_hp": my_hp, 
        "my_max_hp": my_max_hp, 
        "enemy_hp": enemy_hp, 
        "enemy_max_hp": enemy_max_hp
    }
    #return {"my_hp": my_hp, "my_max_hp": my_max_hp, "enemy_hp": enemy_hp, "enemy_max_hp": enemy_max_hp}
# print(get_battle_state())
# print(get_battle_state())
# load_state_file('/Users/hrishishah/MLEngineer/pokegym/fight_save_slot.ss0')# print(send_cmd("core.help"))
import time
addrs = [0x02022B4B, 0x02022B4C, 0x02023BE3, 0x02023BE4]
for addr in addrs:
    val = int(send_cmd(f"core.read8,{addr}"))
    print(f"0x{addr:08X}: {val}")