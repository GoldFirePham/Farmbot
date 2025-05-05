from farmbot import Farmbot
from getpass import getpass
import json
from datetime import datetime
import time
from time import sleep
import math
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import os
import cv2
from tqdm import tqdm
from rich.console import Console
import paho.mqtt.publish as mqtt_publish
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



def execute_weed_detection(fb, issuer, headers, plant_name="Beet", image_folder="weed_images", max_retries=10):
    """
    Captures images, detects plants using OpenCV, converts pixel positions to coordinates, and classifies weeds.
    
    :param fb: FarmBot instance
    :param issuer: API issuer URL
    :param headers: API headers for authentication
    :param plant_name: Target plant name for comparison
    :param image_folder: Directory to store images
    :param max_retries: Max attempts to fetch a new image
    """
    os.makedirs(image_folder, exist_ok=True)

    print("Fetching plant coordinates...")
    response = requests.get(f"{issuer}/api/points", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get plant data: {response.status_code}")
        return

    plants = response.json()
    target_plants = [p for p in plants if p.get("name") == plant_name]

    if not target_plants:
        print(f"No {plant_name} plants found.")
        return

    print(f"Found {len(target_plants)} {plant_name} plants.")

    # Normalize Y-coordinates for row-based scanning
    Y_TOLERANCE = 2
    def normalize_y(y_value): return round(y_value / Y_TOLERANCE) * Y_TOLERANCE

    rows = defaultdict(list)
    for plant in target_plants:
        x, y, z = plant['x'], normalize_y(plant['y']), plant['z']
        rows[y].append((x, y, z))

    sorted_rows = sorted(rows.items())

    # Track movement direction
    zigzag = False
    visited_coordinates = []
    last_image_url = None

    for y, row in sorted_rows:
        zigzag = not zigzag
        row = sorted(row, key=lambda coord: coord[0], reverse=not zigzag)

        for x, y, z in row:
            if (x, y) in visited_coordinates:
                print(f"Skipping already visited coordinates: x={x}, y={y}")
                continue

            print(f"Moving to plant at x={x}, y={y}, z={z}")
            fb.move(x=x, y=y, z=z)
            time.sleep(2)

            print("Capturing image...")
            fb.take_photo()
            time.sleep(10)

            # Ensure we get a new image
            latest_image_url = None
            for attempt in range(max_retries):
                print(f"Fetching latest image... (Attempt {attempt + 1})")
                images_response = requests.get(f"{issuer}/api/images", headers=headers)
                if images_response.status_code != 200:
                    print(f"Failed to get images: {images_response.status_code}")
                    continue

                images = images_response.json()
                if not images:
                    print("No images found.")
                    time.sleep(3)
                    continue

                images = sorted(images, key=lambda img: img['created_at'], reverse=True)
                latest_image = images[0]
                latest_image_url = latest_image["attachment_url"]

                if "placeholder_farmbot.jpg" in latest_image_url:
                    print("Detected placeholder image. Waiting for real image...")
                    time.sleep(5)
                    continue

                if last_image_url and latest_image_url == last_image_url:
                    print("New image matches previous image, retrying...")
                    time.sleep(5)
                    continue

                break

            if not latest_image_url:
                print("Failed to retrieve a new image after retries.")
                continue

            print(f"Downloading new image from {latest_image_url}")

            # Download and save the latest image
            image_response = requests.get(latest_image_url)
            if image_response.status_code == 200:
                img = Image.open(BytesIO(image_response.content))
                file_name = f"{image_folder}/image_X{x}_Y{y}.jpg"
                img.save(file_name)
                print(f"Image saved: {file_name}")

                # Update last image URL
                last_image_url = latest_image_url
            else:
                print(f"Failed to download image: {image_response.status_code}")

            visited_coordinates.append((x, y))

            # 🔥 **Step 2: Detect Plants using OpenCV**
            print("Detecting plants in image using OpenCV...")
            weeds = detect_plants_opencv(file_name)

            # 🔥 **Step 3: Convert Pixels to Coordinates**
            weed_coordinates = convert_pixel_to_coordinates(weeds, x, y)

            # delete old weeds first, max limit for point usage (currently 1000) 
            delete_old_weeds(issuer, headers)

            # 🔥 **Step 4: Classify and Store Weeds**
            save_detected_weeds(weed_coordinates, target_plants, issuer, headers)

            time.sleep(2)
            console.print(f"sleeping...................200", style="bold green")
            # sleep(200)

    print("Finished capturing, detecting, and saving weed data.")


### 🔹 **OpenCV Plant Detection Function**
def detect_plants_opencv(image_path):
    """
    Detects green plant-like areas using OpenCV.
    
    :param image_path: Path to the image file.
    :return: List of detected plant pixel coordinates.
    """
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define green color range
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([90, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    plant_coordinates = [cv2.boundingRect(cnt) for cnt in contours]
    return plant_coordinates


### 🔹 **Convert Pixel Locations to FarmBot Coordinates**
def convert_pixel_to_coordinates(plant_pixels, x_origin, y_origin, scale_factor=0.1):
    """
    Converts detected pixel locations into real-world FarmBot coordinates.
    Now includes width and height information for dynamic radius calculation.
    
    :param plant_pixels: List of plant bounding boxes in pixel coordinates.
    :param x_origin: FarmBot X-coordinate of the image capture location.
    :param y_origin: FarmBot Y-coordinate of the image capture location.
    :param scale_factor: Conversion factor from pixels to FarmBot coordinates.
    :return: List of converted plant coordinates with dimensions.
    """
    weed_coordinates = []
    for (px, py, w, h) in plant_pixels:
        real_x = x_origin + (px * scale_factor)
        real_y = y_origin + (py * scale_factor)
        real_width = w * scale_factor
        real_height = h * scale_factor
        weed_coordinates.append((real_x, real_y, real_width, real_height))

    return weed_coordinates

def delete_old_weeds(issuer, headers, keep_latest=350):
    """
    Deletes old weeds if the FarmBot has hit the max point limit.
    :param issuer: API issuer URL.
    :param headers: API headers for authentication.
    :param keep_latest: Number of recent weeds to keep.
    """
    print("Fetching all points...")

    response = requests.get(f"{issuer}/api/points", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch points: {response.status_code}")
        return
    
    points = response.json()
    weeds = [p for p in points if p.get("pointer_type") == "Weed"]

    print(f"🔍 Found {len(weeds)} weeds stored.")

    if len(weeds) <= keep_latest:
        print("✅ Weed count is within limit. No need to delete.")
        return

    # Sort weeds by creation date (oldest first)
    weeds = sorted(weeds, key=lambda w: w["created_at"])

    # Delete the oldest weeds
    weeds_to_delete = weeds[:-keep_latest]  # Keep only the latest N weeds

    for weed in weeds_to_delete:
        delete_url = f"{issuer}/api/points/{weed['id']}"
        delete_response = requests.delete(delete_url, headers=headers)

        if delete_response.status_code == 200:
            print(f"✅ Deleted weed ID {weed['id']}")
        else:
            print(f"❌ Failed to delete weed ID {weed['id']}: {delete_response.text}")

    print("✅ Old weeds deleted. You can now save new weed points.")




WEED_FILE = "detected_weeds.json"  # ✅ Local file for storing detected weeds
WEED_RADIUS = 50  # ✅ Min distance to consider as a crop
MAX_DISTANCE = 300  # ✅ Ignore weeds detected beyond this range

def save_detected_weeds(weed_coordinates, known_plants, issuer, headers):
    """
    Classifies detected plants as weeds, saves them locally in JSON, and uploads them to FarmBot.
    Now uses dynamic radius based on detected plant dimensions.
    """
    known_positions = [(p['x'], p['y']) for p in known_plants]

    # Add debug logging for coverage area
    for kx, ky in known_positions:
        print(f"\nCoverage area for plant at X:{kx}, Y:{ky}:")
        print(f"X range: {kx-MAX_DISTANCE} to {kx+MAX_DISTANCE}")
        print(f"Y range: {ky-MAX_DISTANCE} to {ky+MAX_DISTANCE}")

    weeds = []
    for wx, wy, width, height in weed_coordinates:
        distances = [np.linalg.norm(np.array([wx, wy]) - np.array([kx, ky])) for kx, ky in known_positions]
        min_distance = min(distances) if distances else float("inf")

        # Calculate dynamic radius based on detected dimensions
        weed_radius = max(width, height) / 2  # Take half of the largest dimension
        # Ensure radius stays within reasonable bounds
        MIN_RADIUS = 5
        MAX_RADIUS = 50
        weed_radius = max(MIN_RADIUS, min(MAX_RADIUS, weed_radius))

        # Only classify as weed if:
        # 1. It is farther than WEED_RADIUS (not near a plant)
        # 2. It is within MAX_DISTANCE (to avoid false positives far away)
        if WEED_RADIUS < min_distance <= MAX_DISTANCE:
            weeds.append({
                "x": wx, 
                "y": wy, 
                "z": 0, 
                "radius": weed_radius
            })

    if not weeds:
        print("✅ No new weeds detected within the valid range.")
        return

    print(f"🔍 Detected {len(weeds)} weeds (within {MAX_DISTANCE} units). Saving locally and uploading...")

    # ✅ FIX: Handle empty JSON file or missing file
    if os.path.exists(WEED_FILE):
        try:
            with open(WEED_FILE, "r") as f:
                existing_weeds = json.load(f)
                if not isinstance(existing_weeds, list):  # Handle corrupted files
                    print("⚠️ Corrupt JSON detected. Resetting weed file.")
                    existing_weeds = []
        except json.JSONDecodeError:
            print("⚠️ Empty or corrupt JSON detected. Resetting weed file.")
            existing_weeds = []
    else:
        existing_weeds = []

    # Append new weeds to the file
    existing_weeds.extend(weeds)

    # Save updated weed list to JSON
    with open(WEED_FILE, "w") as f:
        json.dump(existing_weeds, f, indent=2)
    print(f"✅ Weeds saved locally to {WEED_FILE}")

    # ✅ DELETE OLD WEEDS IF FARMBOT LIMIT IS REACHED
    delete_old_weeds(issuer, headers, keep_latest=100)

    # ✅ UPLOAD TO FARM BOT
    for weed in weeds:
        payload = {
            "name": "Weed",
            "pointer_type": "Weed",
            "x": weed["x"],
            "y": weed["y"],
            "z": weed["z"],
            "radius": weed["radius"],
            "meta": {}  
        }

        print(f"📤 Sending payload: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{issuer}/api/points", json=payload, headers=headers)

        if response.status_code == 200:
            print(f"✅ Weed uploaded successfully: {weed}")
        else:
            print(f"❌ Failed to upload weed: {response.status_code} - {response.text}")

    print("✅ Weed detection and saving process completed.")

execute_weed_detection(fb, issuer, headers, plant_name="Beet", image_folder="weed_images", max_retries=10)