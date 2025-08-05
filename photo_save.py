from farmbot import Farmbot
import json
import os
import requests
from tqdm import tqdm
from rich.console import Console
from datetime import datetime

console = Console()

# FarmBot credentials
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# Authenticate and get token
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

# Save and load token (optional)
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

# Create a directory for today's date
today_str = datetime.now().strftime("%b%d_%Y")  # e.g., Jul01_2025
photo_dir = os.path.join("farmbot_photos", today_str)
os.makedirs(photo_dir, exist_ok=True)

console.print(f"📸 Saving images to: {photo_dir}", style="bold green")
console.print("Fetching all images from FarmBot...", style="bold green")

# Get all images from the API
images_url = f"{SERVER}/api/images"
response = requests.get(images_url, headers=headers)

if response.status_code != 200:
    console.print("❌ Failed to fetch images!", style="bold red")
    exit(1)

images = response.json()
console.print(f"Found {len(images)} images. Starting download and deletion...", style="bold cyan")

# Download and delete each image
for image in tqdm(images, desc="Processing images"):
    img_url = image['attachment_url']
    img_id = image['id']

    # Extract coordinates, fallback if missing
    x = image['meta'].get('x', 'unknownX')
    y = image['meta'].get('y', 'unknownY')
    z = image['meta'].get('z', 'unknownZ')

    # Extract date and time from 'created_at'
    created_at = image.get('created_at', '')
    if created_at:
        dt_obj = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        timestamp_str = dt_obj.strftime("%Y-%m-%d_%H-%M-%S")  # e.g., 2025-07-01_15-30-22
    else:
        timestamp_str = "unknownDateTime"

    # Filename: 2025-07-01_15-30-22_coord.600.500.0.jpg
    img_name = f"{timestamp_str}_coord.{x}.{y}.{z}.jpg"
    img_path = os.path.join(photo_dir, img_name)

    try:
        # Download image
        img_data = requests.get(img_url)
        with open(img_path, 'wb') as f:
            f.write(img_data.content)

        # Delete image from server
        delete_url = f"{SERVER}/api/images/{img_id}"
        del_response = requests.delete(delete_url, headers=headers)

        if del_response.status_code == 200:
            console.print(f"🗑️ Deleted image {img_id}", style="dim")
        else:
            console.print(f"❌ Failed to delete image {img_id}: {del_response.status_code}", style="bold red")

    except Exception as e:
        console.print(f"⚠️ Error processing image {img_id}: {e}", style="bold red")

console.print(f"✅ Downloaded and deleted {len(images)} images.", style="bold green")

