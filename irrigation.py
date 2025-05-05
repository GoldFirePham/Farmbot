from farmbot import Farmbot
from getpass import getpass
import json
from datetime import datetime
import json
import time
from time import sleep
import math
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from farmbot import Farmbot
import os
from tqdm import tqdm
from rich.console import Console
import paho.mqtt.publish as mqtt_publish
import time
from collections import defaultdict

console = Console()


SERVER = 'https://my.farm.bot'
EMAIL = <email>
PASSWORD = <password>


fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)



# save token to file
with open('farmbot_authorization_token.json', 'w') as f:
	f.write(json.dumps(TOKEN))
	print('token saved to file')


# load token from file
with open('farmbot_authorization_token.json', 'r') as f:
	TOKEN = json.load(f)


fb.set_verbosity(2)
peripherals = fb.api_get("peripherals")

fb.set_timeout(240, "movements")

get_config_Details = fb.api_get('web_app_config')


# Extract the encoded token and issuer from the TOKEN dictionary
encoded_token = TOKEN['token']['encoded']
issuer = "https:" + TOKEN['token']['unencoded']['iss']

# Set up headers for authorization
headers = {
	'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
	'Content-Type': "application/json"
}


def get_latest_soil_moisture(headers):
	headers = {
		'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
		'Content-Type': "application/json"
	}

	pin25 = fb.read_pin(59, "analog")
	fb.read_sensor("Soil Moisture")
	sleep(5)

	readings_response = requests.get(f"{issuer}/api/sensor_readings", headers=headers)
	print(readings_response)

	# Check if the request was successful
	if readings_response.status_code == 200:
		readings = readings_response.json()
		print(readings[0]['value'])
		return readings[0]['value']
	else:
		print(f"Failed to get sensor readings: {readings_response.status_code}")


console.print(f"Adjusting to original position......", style="bold red")
fb.move(z=0)


# Tolerance for grouping Y-coordinates into rows
Y_TOLERANCE = 2
# Function to normalize Y-coordinate into consistent rows
def normalize_y(y_value):
	return round(y_value / Y_TOLERANCE) * Y_TOLERANCE

# Get all points from the FarmBot API
response = requests.get(f"https:{TOKEN['token']['unencoded']['iss']}/api/points", headers=headers)

# Check if the request was successful
if response.status_code == 200:
	points = response.json()
else:
	print(f"Failed to get points: {response.status_code}")
	exit(1)

# Filter points for plants named "Beet" and extract coordinates
beet_plants = [point for point in points if point.get("name") == "Beet"]

if len(beet_plants) == 0:
	print("No Beet plants found.")
	exit(0)

console.print(f"Found {len(beet_plants)} Beet plants.", style="bold red")

# Normalize and group coordinates by Y-axis (rows) with tolerance
rows = defaultdict(list)
for plant in beet_plants:
	x = plant['x']
	y = normalize_y(plant['y'])  # Normalize Y-coordinate
	z = plant['z']
	rows[y].append((x, y, z))

# Sort rows by Y-axis (ascending)
sorted_rows = sorted(rows.items())

# Track movement direction
zigzag = False

# Keep track of visited coordinates for debugging
visited_coordinates = []

# Loop through each row in the grid
for y, row in sorted_rows:
	# Toggle zigzag direction for each row
	zigzag = not zigzag

	# Log the row's coordinates before sorting
	print(f"\nProcessing Row at Y={y} with Coordinates: {row}")

	# Sort the row based on zigzag direction
	if zigzag:
		row = sorted(row, key=lambda coord: coord[0])  # Left to right
	else:
		row = sorted(row, key=lambda coord: coord[0], reverse=True)  # Right to left

	# Log the sorted coordinates for this row
	print(f"Row {y} Sorted Coordinates (Zigzag={zigzag}): {row}")

	# Move through each point in the current row
	for x, y, z in row:
		if (x, y) in visited_coordinates:
			print(f"Skipping already visited coordinates: x={x}, y={y}")
			continue

		print(f"Moving to Beet plant at coordinates: x={x}, y={y}, z={z}")
		
		# Move to the current coordinate
		fb.move(x=x, y=y, z=z)
		
		# Mark the coordinates as visited
		visited_coordinates.append((x, y))

		take_photo = fb.take_photo()
		console.print(f'Taking Picture........', style="bold red")
		print(take_photo)
		time.sleep(2)

		# Lower Z-axis to -500
		z = -500
		console.print(f"Lowering Z-axis to {z} and Y-axis to {y+40}...", style="bold green")
		fb.move(x=x, y=y+40, z=z)
		print('sleeeping for 4 secs')
		time.sleep(4)
		print("Z-axis lowered. Collecting soil moisture reading...")
		print("getting soil data........================")
		x_axis=x
		y_axis=y

		latest_soil_value = get_latest_soil_moisture(headers)
		console.print(f"Latest Soil Moisture Value from Pin 59: {latest_soil_value}", style="bold red")
		console.print(f'sleeping for 1 secs', style="bold red")
		time.sleep(1)



		# moving Z-axis half way up to -200
		z = -200
		console.print(f"Moving Z-axis half way up to {z} for watering......", style="bold red")
		fb.move(x=x, y=y+40, z=z)
		print('sleeeping for 4 secs')
		time.sleep(4)

		if latest_soil_value < 10:
			turn_on_water = fb.on(8)
			console.print(f'turning_on_water..........', style="bold red")
			time.sleep(2)
			turn_on_water = fb.off(8)
			console.print(f'turning_off_water..........', style="bold red")
			time.sleep(2)
		else:
			console.print(f'Moisture levels are adequate, skipping irrigation...........', style="bold red")

		
		# Dispense 200 mL of fertilizer using a custom tool operated by pin 7
		# fb.dispense(200, tool_name="Custom Watering Nozzle 2", pin=7)


		# turn_off_water = fb.off(8)
		# print(turn_off_water)
		# time.sleep(2)
		# Wait for 10 seconds before moving to the next plant
		# for i in 10:
		# 	fb.take_photo()
		# fb.dispense(100)
		# time.sleep(1)

		# Raise Z-axis back to safe position
		z = 0
		print(f"Raising Z-axis back to {z}...")
		fb.move(x=x, y=y, z=z)
		console.print(f"Z-axis raised.....", style="bold red")
		time.sleep(2)

print("Finished moving to all Beet plants.")