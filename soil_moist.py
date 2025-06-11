from farmbot import Farmbot
import time
import csv
from datetime import datetime
from rich.console import Console

# === FarmBot Login Info ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot
MOISTURE_SENSOR_PIN = 59  # Replace with your actual sensor pin

# === Grid configuration ===
X_START = 600
X_END = 5600
Y_START = 500
Y_END = 2500
X_STEP = 1000
Y_STEP = 1000

# === Setup ===
console = Console()
fb = Farmbot()
fb.login(email=EMAIL, password=PASSWORD)

# === CSV Setup ===
today = datetime.now().strftime("%b%d.%Y")
filename = f"soil_grid_readings_{today}.csv"

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'X', 'Y', 'Soil Moisture'])

    # === Generate grid and collect data ===
    for y in range(Y_START, Y_END + 1, Y_STEP):
        for x in range(X_START, X_END + 1, X_STEP):
            console.print(f"\n📍 Moving to ({x}, {y})", style="bold green")
            fb.move(x=x, y=y, z=0)
            time.sleep(5)  # Wait for stabilization

            # === Read from sensor ===
            moisture = fb.read_pin(MOISTURE_SENSOR_PIN, mode='analog')
            timestamp = datetime.now().isoformat()

            writer.writerow([timestamp, x, y, moisture])
            console.print(f"🌱 Moisture at ({x}, {y}): {moisture}", style="cyan")

console.print(f"\n✅ Soil moisture grid scan complete. Data saved to {filename}", style="bold blue")
