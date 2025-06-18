from farmbot import Farmbot
import time
import csv
from datetime import datetime
from rich.console import Console

# === FarmBot Credentials ===
SERVER = 'https://my.farm.bot'
EMAIL = 'pjesuraj@umes.edu'
PASSWORD = 'umesfarmbot'
MOISTURE_SENSOR_PIN = 59  # Analog sensor pin number

# === Grid Configuration ===
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

# === CSV Output Setup ===
today = datetime.now().strftime("%b%d.%Y")
filename = f"soil_grid_readings_{today}.csv"

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'X', 'Y', 'Soil Moisture'])

    for y in range(Y_START, Y_END + 1, Y_STEP):
        for x in range(X_START, X_END + 1, X_STEP):
            console.print(f"\n📍 Moving to ({x}, {y}, z=0)", style="bold green")
            fb.move(x=x, y=y, z=0)
            time.sleep(5)  # Let FarmBot settle at position

            # Step 1: Offset downward to insert probe
            console.print("📉 Lowering probe into soil", style="yellow")
            fb.move_relative(x=-50, y=0, z=-536)
            time.sleep(1)

            # Step 2: Read moisture sensor
            console.print("🔍 Reading soil moisture...", style="cyan")
            moisture = fb.read_pin(MOISTURE_SENSOR_PIN, mode='analog')
            time.sleep(1)

            # Step 3: Lift probe back up
            console.print("📈 Lifting probe", style="yellow")
            fb.move_relative(x=0, y=0, z=200)
            time.sleep(1)

            # Step 4: Log data
            timestamp = datetime.now().isoformat()
            writer.writerow([timestamp, x, y, moisture])
            console.print(f"🌱 Moisture at ({x}, {y}): {moisture}", style="cyan")

console.print(f"\n✅ Scan complete. Data saved to {filename}", style="bold blue")

