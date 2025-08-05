from farmbot import Farmbot
import json
import time
import requests
import os
from tqdm import tqdm
from rich.console import Console
from datetime import datetime

console = Console()

# === FarmBot Credentials ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'

# === Authenticate ===
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

# Save and load token
with open('farmbot_authorization_token.json', 'w') as f:
    json.dump(TOKEN, f)
with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

fb.set_verbosity(2)

# === Setup headers ===
HEADERS = {
    'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
    'Content-Type': "application/json"
}

# === Move to (0, 0, 0) ===
console.print("🏁 Moving to (0, 0, 0)...", style="bold red")
fb.move(x=0, y=0, z=0)
time.sleep(5)

# === Get point groups ===
group_response = requests.get(f"{SERVER}/api/point_groups", headers=HEADERS)
if group_response.status_code != 200:
    console.print("❌ Failed to fetch point groups", style="bold red")
    exit(1)
point_groups = group_response.json()

# === Display group list ===
console.print("\n📋 Available Point Groups:", style="bold green")
for idx, group in enumerate(point_groups):
    console.print(f"[{idx}] {group['name']}")

# === Let user pick group ===
selected_idx = int(input("\n➡️  Enter the number of the group you want to scan: "))
selected_group = point_groups[selected_idx]
group_point_ids = selected_group['point_ids']
console.print(f"\n🌱 Selected Group: [bold]{selected_group['name']}[/bold]", style="green")

# === Get all points ===
points_response = requests.get(f"{SERVER}/api/points", headers=HEADERS)
if points_response.status_code != 200:
    console.print("❌ Failed to fetch points", style="bold red")
    exit(1)

all_points = points_response.json()
points_to_visit = [pt for pt in all_points if pt['id'] in group_point_ids]
points_to_visit.sort(key=lambda p: (p['x'], p['y']))

# === Setup output directory ===
today = datetime.today().strftime('%b%d.%Y')
output_dir = f"farmbot_photos/{today}"
os.makedirs(output_dir, exist_ok=True)

# === Visit points and take pictures ===
visited_coords = []
console.print(f"\n📷 Scanning {len(points_to_visit)} points in group...", style="bold green")
for pt in tqdm(points_to_visit):
    x, y, z = pt["x"], pt["y"], pt["z"]
    console.print(f"➡️  Moving to ({x}, {y}, {z})", style="cyan")
    fb.move(x=x, y=y, z=z)
    time.sleep(3)

    console.print("📸 Taking photo...", style="yellow")
    fb.take_photo()
    visited_coords.append((x, y, z))
    time.sleep(2)

# === Download today's photos ===
console.print("\n⬇️  Downloading today’s photos...", style="bold green")
image_response = requests.get(f"{SERVER}/api/images", headers=HEADERS)

if image_response.status_code != 200:
    console.print("❌ Failed to fetch images", style="bold red")
    exit(1)

all_images = image_response.json()
today_prefix = datetime.today().strftime('%Y-%m-%d')
todays_images = [img for img in all_images if img["created_at"].startswith(today_prefix)]
todays_images = sorted(todays_images, key=lambda x: x["created_at"])

# === Save images ===
for coord, img in zip(visited_coords, todays_images):
    x, y, z = coord
    url = img["attachment_url"]
    filename = f"coor.{x}.{y}.{z}.jpg"
    save_path = os.path.join(output_dir, filename)

    img_data = requests.get(url)
    with open(save_path, "wb") as f:
        f.write(img_data.content)

    console.print(f"✅ Saved {save_path}", style="green")

console.print(f"\n✅ All photos saved in: {output_dir}", style="bold green")

