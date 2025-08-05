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
console.print("🔁 Moving to (0, 0, 0) to reset position...", style="bold red")
fb.move(x=0, y=0, z=0)
time.sleep(5)

# === Fetch all point groups ===
console.print("📦 Fetching point groups from FarmBot...", style="bold magenta")

group_response = requests.get(f"{SERVER}/api/point_groups", headers=HEADERS)
if group_response.status_code != 200:
    console.print(f"❌ Failed to retrieve point groups: {group_response.status_code}", style="bold red")
    exit(1)

point_groups = group_response.json()

# === Display point group names ===
console.print("\n📋 Available Point Groups:", style="bold green")
for idx, group in enumerate(point_groups):
    console.print(f"[{idx}] {group['name']}")

# === Ask user to select group ===
selected_idx = int(input("\n➡️  Enter the number of the group you want to water: "))
selected_group = point_groups[selected_idx]
group_point_ids = selected_group['point_ids']

console.print(f"\n🌱 Selected Group: [bold]{selected_group['name']}[/bold]", style="green")

# === Fetch all points ===
points_response = requests.get(f"{SERVER}/api/points", headers=HEADERS)
if points_response.status_code != 200:
    console.print(f"❌ Failed to retrieve points: {points_response.status_code}", style="bold red")
    exit(1)

all_points = points_response.json()
points_to_water = [pt for pt in all_points if pt['id'] in group_point_ids]

# === Sort by (x, y) if needed ===
points_to_water.sort(key=lambda p: (p['x'], p['y']))

# === Water each point ===
for point in points_to_water:
    x, y, z = point['x'], point['y'], point['z']
    name = point.get('name', 'Unnamed')

    console.print(f"\n📍 Moving to {name} at ({x}, {y}, {z})", style="bold cyan")
    fb.move(x=x, y=y, z=z)
    time.sleep(3)

    console.print(f"💧 Turning ON water at ({x}, {y})...", style="bold blue")
    fb.write_pin(pin_number=8, mode='digital', value=1)
    time.sleep(50)

    console.print(f"🚫 Turning OFF water at ({x}, {y})...", style="bold blue")
    fb.write_pin(pin_number=8, mode='digital', value=0)
    time.sleep(2)

console.print(f"\n✅ Watering complete for group: [bold]{selected_group['name']}[/bold]", style="bold green")

