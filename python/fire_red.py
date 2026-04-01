import socket

s = socket.socket()
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

print(get_player_state())