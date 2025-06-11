from farmbot import Farmbot
import json
import os
import time
import requests
from datetime import datetime
from tqdm import tqdm
from rich.console import Console
from PIL import Image

console = Console()

# FarmBot credentials
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# === Grid configuration ===
X_START = 600
X_END = 5600
Y_START = 500
Y_END = 2500
X_STEP = 1000
Y_STEP = 1000

# Initialize Farmbot and authenticate
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

with open('farmbot_authorization_token.json', 'w') as f:
    json.dump(TOKEN, f)

with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

fb.set_verbosity(2)

headers = {
    'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
    'Content-Type': "application/json"
}

# Prepare date-based directory
date_str = datetime.now().strftime("%b%d.%Y")
photo_dir = os.path.join("farmbot_photos", date_str)
os.makedirs(photo_dir, exist_ok=True)

console.print(f"Scanning bed with step size X:{X_STEP}, Y:{Y_STEP}...", style="bold green")

# Create scan positions
positions = []
for y in range(Y_START, Y_END + 1, Y_STEP):
    for x in range(X_START, X_END + 1, X_STEP):
        positions.append((x, y))

# Move and take photo at each position
for (x, y) in tqdm(positions, desc="Scanning grid"):
    console.print(f"Moving to ({x}, {y})", style="bold cyan")
    fb.move(x=x, y=y, z=0)
    time.sleep(5)
    console.print("Capturing image...", style="dim")
    fb.take_photo()
    time.sleep(10)

# Download today's photos
console.print("Fetching today's images...", style="bold green")
images_url = f"{SERVER}/api/images"
response = requests.get(images_url, headers=headers)

if response.status_code != 200:
    console.print("Failed to fetch images!", style="bold red")
    exit(1)

images = response.json()
today_str = datetime.now().strftime("%Y-%m-%d")
images_today = [img for img in images if img.get('created_at', '').startswith(today_str)]

console.print(f"Found {len(images_today)} images.", style="bold cyan")

# Download photos
for img in tqdm(images_today, desc="Downloading"):
    url = img['attachment_url']
    meta = img.get('meta', {})
    x = meta.get('x', 'x')
    y = meta.get('y', 'y')
    img_id = img['id']
    name = f"coor_{x}_{y}_{img_id}.jpg"
    path = os.path.join(photo_dir, name)
    try:
        data = requests.get(url)
        with open(path, 'wb') as f:
            f.write(data.content)
    except Exception as e:
        console.print(f"Download failed: {e}", style="bold red")

# Stitch images
cols = ((X_END - X_START) // X_STEP) + 1
rows = ((Y_END - Y_START) // Y_STEP) + 1

images_dict = {}
for img in images_today:
    meta = img.get('meta', {})
    x = meta.get('x')
    y = meta.get('y')
    img_id = img['id']
    name = f"coor_{x}_{y}_{img_id}.jpg"
    path = os.path.join(photo_dir, name)
    if os.path.exists(path):
        images_dict[(x, y)] = Image.open(path)

sample_img = next(iter(images_dict.values()))
img_w, img_h = sample_img.size

stitched_img = Image.new('RGB', (cols * img_w, rows * img_h))

for row_i, y in enumerate(range(Y_START, Y_END + 1, Y_STEP)):
    for col_i, x in enumerate(range(X_START, X_END + 1, X_STEP)):
        img = images_dict.get((x, y))
        if img:
            stitched_img.paste(img, (col_i * img_w, row_i * img_h))

stitched_path = os.path.join(photo_dir, f"stitched_bed_{date_str}.jpg")
stitched_img.save(stitched_path)

console.print(f"Stitched image saved to {stitched_path}", style="bold green")
