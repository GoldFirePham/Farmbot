from farmbot import Farmbot
from getpass import getpass
import json
import time
from datetime import datetime
import requests
from collections import defaultdict
from tqdm import tqdm
from rich.console import Console

console = Console()

# Configuration
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'
PIN_SOIL_MOISTURE = 59
PIN_WATER = 8
Y_TOLERANCE = 2

# Initialize FarmBot and authenticate
fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)

# Save token to file
with open('farmbot_authorization_token.json', 'w') as f:
    json.dump(TOKEN, f)
    print('Token saved to file')

# Set up headers for authorization
encoded_token = TOKEN['token']['encoded']
issuer = "https:" + TOKEN['token']['unencoded']['iss']
headers = {
    'Authorization': f'Bearer {encoded_token}',
    'Content-Type': 'application/json'
}

fb.set_verbosity(2)
fb.set_timeout(240, "movements")

# Helper function to normalize Y-coordinate
def normalize_y(y_value):
    return round(y_value / Y_TOLERANCE) * Y_TOLERANCE

# Get latest soil moisture value
def get_latest_soil_moisture(headers):
    fb.read_pin(PIN_SOIL_MOISTURE, "analog")
    fb.read_sensor("Soil Moisture")
    time.sleep(5)

    readings_response = requests.get(f"{issuer}/api/sensor_readings", headers=headers)
    if readings_response.status_code == 200:
        readings = readings_response.json()
        return readings[0]['value']
    else:
        print(f"Failed to get sensor readings: {readings_response.status_code}")
        return None

# Move FarmBot to home Z position
console.print(f"Adjusting to original position...", style="bold red")
fb.move(z=0)

# Retrieve all plant points
response = requests.get(f"{issuer}/api/points", headers=headers)
if response.status_code != 200:
    print(f"Failed to get points: {response.status_code}")
    exit(1)

points = response.json()
plant_name = 'Green Zucchini'
target_plants = [p for p in points if p.get("name") == plant_name]

if not target_plants:
    print(f"No {plant_name} plants found.")
    exit(0)

console.print(f"Found {len(target_plants)} {plant_name} plants.", style="bold red")

# Group and sort plants by normalized Y-axis
rows = defaultdict(list)
for plant in target_plants:
    x, y, z = plant['x'], plant['y'], plant['z']
    norm_y = normalize_y(y)
    rows[norm_y].append((x, y, z))

sorted_rows = sorted(rows.items())
zigzag = False
visited_coordinates = []

# Process each row and plant
for y, row in sorted_rows:
    zigzag = not zigzag
    row = sorted(row, key=lambda coord: coord[0], reverse=not zigzag)
    print(f"\nProcessing Row at Y={y} with Coordinates: {row}")

    for x, y, z in row:
        if (x, y) in visited_coordinates:
            print(f"Skipping already visited coordinates: x={x}, y={y}")
            continue

        console.print(f"Moving to {plant_name} plant at x={x}, y={y}, z={z}", style="bold green")
        fb.move(x=x, y=y, z=z)
        visited_coordinates.append((x, y))

        fb.take_photo()
        time.sleep(2)

        # Lower Z to soil level
        z = -500
        fb.move(x=x, y=y+40, z=z)
        time.sleep(4)

        console.print("Collecting soil moisture reading...", style="bold blue")
        latest_soil_value = get_latest_soil_moisture(headers)

        if latest_soil_value is not None:
            console.print(f"Soil Moisture: {latest_soil_value}", style="bold red")
        else:
            continue

        # Raise Z partway
        z = -200
        fb.move(x=x, y=y+40, z=z)
        time.sleep(4)

        if latest_soil_value < 10:
            fb.on(PIN_WATER)
            time.sleep(10)
            fb.off(PIN_WATER)
            console.print("Water applied.", style="bold cyan")
        else:
            console.print("Moisture adequate. Skipping watering.", style="bold yellow")

        # Raise Z to safe height
        z = 0
        fb.move(x=x, y=y, z=z)
        time.sleep(2)

console.print(f"Finished watering all {plant_name} plants.", style="bold green")

