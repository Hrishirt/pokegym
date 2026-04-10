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
    base = 0x02024284
    my_hp = int(send_cmd(f"core.read16,{base + 0x56}"))
    my_max_hp = int(send_cmd(f"core.read16,{base + 0x58}"))
    enemy_hp = int(send_cmd(f"core.read16,{0x02024090 + 0x56}"))
    enemy_max_hp = int(send_cmd(f"core.read16,{0x02024090 + 0x58}"))
    return {"my_hp": my_hp, "my_max_hp": my_max_hp, "enemy_hp": enemy_hp, "enemy_max_hp": enemy_max_hp}
print(get_battle_state())