from farmbot import Farmbot
import json
import time
import requests
import os
from tqdm import tqdm
from rich.console import Console
from datetime import datetime

console = Console()

# === FarmBot credentials ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# === Authenticate and get token ===
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

# Save token
with open('farmbot_authorization_token.json', 'w') as f:
    json.dump(TOKEN, f)

# Load token
with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

fb.set_verbosity(2)

# Setup authorization headers
HEADERS = {
    'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
    'Content-Type': "application/json"
}

# === Move to (0, 0, 0) to reset position ===
console.print("Moving to (0, 0, 0) to reset position...", style="bold red")
fb.move(x=0, y=0, z=0)
time.sleep(5)

# === Grid Configuration ===
X_START = 600
X_END = 5600
Y_START = 500
Y_END = 2500
STEP_SIZE = 1000

x_range = list(range(X_START, X_END + 1, STEP_SIZE))
y_range = list(range(Y_START, Y_END + 1, STEP_SIZE))

# === Start irrigation routine ===
console.print(f"Starting irrigation routine...", style="bold green")

zigzag = False

for y in y_range:
    zigzag = not zigzag
    row = x_range if zigzag else list(reversed(x_range))

    for x in row:
        z = 0
        console.print(f"Moving to ({x}, {y}, {z})...", style="bold cyan")
        fb.move(x=x, y=y, z=z)
        time.sleep(3)

        # === Turn on water ===
        console.print(f"💧 Turning ON water at ({x}, {y})...", style="bold blue")
        fb.write_pin(pin_number=8, mode='digital', value=1)  # Assumes pin 8 is water valve
        time.sleep(50)

        # === Turn off water ===
        console.print(f"🚫 Turning OFF water at ({x}, {y})...", style="bold blue")
        fb.write_pin(pin_number=8, mode='digital', value=0)
        time.sleep(2)

console.print(f"✅ Irrigation routine complete.", style="bold green bold")

