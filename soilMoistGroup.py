from farmbot import Farmbot
import time
import csv
import requests
from datetime import datetime
from rich.console import Console

# === FarmBot Credentials ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'
MOISTURE_SENSOR_PIN = 59  # Analog pin for soil moisture sensor

# === Authenticate and get token ===
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# === Probe Movement Offsets ===
X_OFFSET = -50      # Shift left for probe
PROBE_DEPTH = -500  # Probe insert depth (Z)
RAISE_HEIGHT = 200  # Raise back up by 200 mm

# === Setup ===
console = Console()

# === Move to (0, 0, 0) to reset position ===
console.print("🔄 Moving to (0, 0, 0) to reset position...", style="bold red")
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
selected_idx = int(input("\n➡️  Enter the number of the group you want to scan for soil moisture: "))
selected_group = point_groups[selected_idx]
group_point_ids = selected_group['point_ids']

console.print(f"\n🌱 Selected Group: [bold]{selected_group['name']}[/bold]", style="green")

# === Fetch all points ===
points_response = requests.get(f"{SERVER}/api/points", headers=HEADERS)
if points_response.status_code != 200:
    console.print(f"❌ Failed to retrieve points: {points_response.status_code}", style="bold red")
    exit(1)

all_points = points_response.json()
points_to_scan = [pt for pt in all_points if pt['id'] in group_point_ids]

# === Sort by (x, y) if needed ===
points_to_scan.sort(key=lambda p: (p['x'], p['y']))

# === CSV Output Setup ===
today = datetime.now().strftime("%b%d.%Y")
filename = f"soil_group_readings_{selected_group['name'].replace(' ', '_')}_{today}.csv"

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'X', 'Y', 'Soil Moisture'])

    for pt in points_to_scan:
        x = pt['x']
        y = pt['y']

        console.print(f"\n📍 Moving to ({x}, {y}, z=0)", style="bold green")
        fb.move(x=x, y=y, z=0)
        time.sleep(5)

        # Absolute coordinates for probe
        probe_x = x + X_OFFSET
        probe_y = y
        probe_z = PROBE_DEPTH

        # Step 1: Lower probe
        console.print("📉 Lowering probe into soil (absolute)", style="yellow")
        fb.move(x=probe_x, y=probe_y, z=probe_z)
        time.sleep(1)

        # Step 2: Read soil moisture
        console.print("🔍 Reading soil moisture...", style="cyan")
        moisture = fb.read_pin(MOISTURE_SENSOR_PIN, mode='analog')
        time.sleep(1)

        # Step 3: Raise probe back up
        console.print("📈 Lifting probe", style="yellow")
        fb.move(x=probe_x, y=probe_y, z=probe_z + RAISE_HEIGHT)
        time.sleep(1)

        # Step 4: Log the reading
        timestamp = datetime.now().isoformat()
        writer.writerow([timestamp, x, y, moisture])
        console.print(f"🌱 Moisture at ({x}, {y}): {moisture}", style="cyan")

console.print(f"\n✅ Soil scan complete. Data saved to {filename}", style="bold blue")

