from farmbot import Farmbot
import json
import os
import time
import requests
from datetime import datetime
from tqdm import tqdm
from rich.console import Console
import cv2

console = Console()

# === FarmBot credentials ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# === Linear scan configuration (X direction only) ===
X_START = 600
X_END = 5600
Y_FIXED = 1500   # Single Y position for panoramic scan
X_STEP = 1000    # Ensure enough overlap between photos

# === Authenticate with FarmBot ===
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

# === Create date-based folder ===
date_str = datetime.now().strftime("%b%d.%Y")
photo_dir = os.path.join("farmbot_photos", date_str)
os.makedirs(photo_dir, exist_ok=True)

# === Scan horizontally across bed ===
positions = [x for x in range(X_START, X_END + 1, X_STEP)]

console.print(f"Starting panoramic scan across X from {X_START} to {X_END} at Y={Y_FIXED}", style="bold green")

for x in tqdm(positions, desc="Capturing"):
    console.print(f"Moving to X={x}, Y={Y_FIXED}", style="bold cyan")
    fb.move(x=x, y=Y_FIXED, z=0)
    time.sleep(5)

    console.print("Taking photo...", style="dim")
    fb.take_photo()
    time.sleep(10)

# === Download today's images ===
console.print("Downloading today's images...", style="bold green")

images_url = f"{SERVER}/api/images"
response = requests.get(images_url, headers=headers)

if response.status_code != 200:
    console.print("Failed to fetch images!", style="bold red")
    exit(1)

images = response.json()
today_str = datetime.now().strftime("%Y-%m-%d")
images_today = [img for img in images if img.get('created_at', '').startswith(today_str)]

downloaded_paths = []

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
        downloaded_paths.append(path)
    except Exception as e:
        console.print(f"Download failed: {e}", style="bold red")

# === Stitch images using OpenCV ===
console.print("Stitching images into panorama...", style="bold green")

# Load images in filename-sorted order
images_cv = []
for path in sorted(downloaded_paths):
    img = cv2.imread(path)
    if img is not None:
        images_cv.append(img)

if len(images_cv) < 2:
    console.print("Not enough images to stitch.", style="bold red")
    exit(1)

stitcher = cv2.Stitcher_create()
status, pano = stitcher.stitch(images_cv)

if status == cv2.Stitcher_OK:
    pano_path = os.path.join(photo_dir, f"panoramic_stitched_{date_str}.jpg")
    cv2.imwrite(pano_path, pano)
    console.print(f"Panoramic stitched image saved to: {pano_path}", style="bold green")
else:
    console.print(f"Stitching failed with error code: {status}", style="bold red")

