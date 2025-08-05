from farmbot import Farmbot
import time
import csv
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

# === Grid Configuration ===
X_START = 600
X_END = 5600
Y_START = 500
Y_END = 2500
X_STEP = 1000
Y_STEP = 1000

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
            time.sleep(5)

            # === Absolute coordinates for probe
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

