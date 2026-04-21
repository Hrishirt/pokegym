import json 
import requests 
import ollama 

from fire_red import get_player_state

# Getting the model we got 
model = "llava:latest"

# Basic function to test and generate a response from the model 
# Edited the code out since we are no longer using memory for movements.
'''
def generate_response(game_state):
    prompt = f"""You are a navigation agent for the game FireRed. You are given the following game state: 
    {game_state['x']}, {game_state['y']}, {game_state['map_bank']}, {game_state['map_num']}. 
    What is the next action you should take? You can only move up, down, left, right."""
    response = ollama.chat(model, [{"role": "user", "content": prompt}])
    return response.message.content

def location_finder(game_state, place):
    prompt = f"""You are controlling a character in Pokemon FireRed.
                Current location: {place}
                Goal: Reach Pewter City Gym.
                Respond with ONLY one word. No explanation. No punctuation. Just the direction.
                Choose one: Up, Down, Left, Right"""
    response = ollama.chat(model, [{"role": "user", "content": prompt}], options={"num_predict": 10})
    return response.message.content

MAP_NAMES = {
    (0, 3): "Pallet Town",
    (19, 3): "Route 1",
}

def get_map_name(map_bank, map_num):
    return MAP_NAMES.get((map_bank, map_num), f"Unknown Map {map_bank}.{map_num}")

state = get_player_state()
location = get_map_name(state['map_bank'], state['map_num'])
print(location)
print(location_finder(state, location))
''' 

# Based off the image, generate a prompt to the model to determine the next action. 
def generate_image_prompt(image_path):
    prompt = """This is a screenshot from Pokemon FireRed.
                The player character is the person in the red hat in the center of the screen.
                The path goes north (up).
                Reply with ONLY one word: Up, Down, Left, or Right.
                Which direction should the player move to follow the path?"""
    response = ollama.chat(model, [
        {
            "role": "user", 
            "content": prompt,
            "images": [image_path]
        }
    ])
    return response.message.content
response = generate_image_prompt("/Users/hrishishah/MLEngineer/pokegym/images/screen.png")
print(response)

