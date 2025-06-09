from farmbot import Farmbot
import json
import time
import requests
from tqdm import tqdm
from rich.console import Console

console = Console()

# FarmBot credentials
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# Authenticate and get token
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

# Save and load token (optional, for reuse)
with open('farmbot_authorization_token.json', 'w') as f:
    json.dump(TOKEN, f)

with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

fb.set_verbosity(2)

# Set up headers
headers = {
    'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
    'Content-Type': "application/json"
}

# Grid configuration
X_START = 600
X_END = 5600
Y_START = 500
Y_END = 2500
X_STEP = 1000
Y_STEP = 1000

# Move to (0, 0) first
console.print("Moving to (0, 0) to reset position...", style="bold red")
fb.move(x=0, y=0, z=0)
time.sleep(5)

# Move to scanning start position
console.print(f"Moving to starting scan position ({X_START}, {Y_START})...", style="bold red")
fb.move(x=X_START, y=Y_START, z=0)
time.sleep(5)

console.print("Starting bed scan and image capture...", style="bold green")

x_range = list(range(X_START, X_END + 1, X_STEP))
y_range = list(range(Y_START, Y_END + 1, Y_STEP))

zigzag = False
photo_count = 0

for y in y_range:
    zigzag = not zigzag
    current_x_range = x_range if zigzag else list(reversed(x_range))

    for x in current_x_range:
        console.print(f"Moving to ({x}, {y})...", style="bold cyan")
        fb.move(x=x, y=y, z=0)
        time.sleep(3)

        console.print(f"Taking picture at ({x}, {y})", style="bold yellow")
        response = fb.take_photo()
        print(response)
        photo_count += 1
        time.sleep(2)

console.print(f"✅ Bed scan complete. Total photos taken: {photo_count}", style="bold green")
