from farmbot import Farmbot
import json
import time
import requests
import os
from tqdm import tqdm
from rich.console import Console
from datetime import datetime

console = Console()

# FarmBot credentials
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

# === Prepare output directory ===
today = datetime.today().strftime('%b%d.%Y')
output_dir = f"farmbot_photos/{today}"
os.makedirs(output_dir, exist_ok=True)

# === Start scan ===
console.print(f"Starting bed scan...", style="bold green")

visited_coords = []
zigzag = False

for y in y_range:
    zigzag = not zigzag
    row = x_range if zigzag else list(reversed(x_range))

    for x in row:
        z = 0
        console.print(f"Moving to ({x}, {y}, {z})...", style="bold cyan")
        fb.move(x=x, y=y, z=z)
        time.sleep(3)

        console.print(f"Taking picture at ({x}, {y})...", style="bold yellow")
        fb.take_photo()
        visited_coords.append((x, y, z))
        time.sleep(2)

console.print(f"Scan complete. Downloading all photos...", style="bold green")

# === Download all images after scan ===
image_response = requests.get("https://my.farm.bot/api/images", headers=HEADERS)

if image_response.status_code != 200:
    console.print("Failed to retrieve image list.", style="bold red")
    exit(1)

all_images = image_response.json()

# Filter today's images only
today_prefix = datetime.today().strftime('%Y-%m-%d')
todays_images = [img for img in all_images if img["created_at"].startswith(today_prefix)]

# Sort by created time just in case
todays_images = sorted(todays_images, key=lambda x: x["created_at"])

# Match coordinates to images (assumes order is preserved)
for coord, img in zip(visited_coords, todays_images):
    x, y, z = coord
    url = img["attachment_url"]
    filename = f"coor.{x}.{y}.{z}.jpg"
    save_path = os.path.join(output_dir, filename)

    img_data = requests.get(url)
    with open(save_path, "wb") as f:
        f.write(img_data.content)
    console.print(f"Saved {save_path}", style="bold green")

console.print(f"All images saved to: {output_dir}", style="bold green bold")

