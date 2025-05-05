# FarmBot Automation System

This project implements an automated farming system using FarmBot, featuring weed detection, irrigation, and plant monitoring capabilities.

## Project Structure

The system consists of two main components:

1. `weed_detection.py` - Handles automated weed detection and management
2. `irrigation.py` - Manages automated irrigation based on soil moisture

## Components

### Weed Detection System (`weed_detection.py`)

The weed detection system uses computer vision to identify and manage weeds around crops. Key features:

- **Plant Detection**: Uses OpenCV to detect green plant-like areas in images
- **Coordinate Conversion**: Converts pixel coordinates to FarmBot coordinates
- **Weed Classification**: Identifies weeds based on distance from known plants
- **Dynamic Radius**: Adjusts weed detection radius based on plant size
- **Weed Management**: Automatically deletes old weed records to maintain system limits

#### Key Functions:
- `detect_plants_opencv()`: Detects plants using color-based segmentation
- `convert_pixel_to_coordinates()`: Converts image coordinates to FarmBot coordinates
- `save_detected_weeds()`: Saves and uploads detected weeds to FarmBot
- `delete_old_weeds()`: Manages weed storage limits

### Irrigation System (`irrigation.py`)

The irrigation system monitors soil moisture and provides automated watering:

- **Soil Moisture Monitoring**: Reads moisture levels from sensors
- **Automated Watering**: Triggers irrigation when moisture levels are low
- **Smart Movement**: Navigates between plants efficiently
- **Zigzag Pattern**: Optimizes movement between rows

#### Key Functions:
- `get_latest_soil_moisture()`: Reads soil moisture sensor data
- Automated irrigation based on moisture thresholds
- Efficient plant-to-plant movement system

## Configuration

### Authentication

Before using the system, you need to update your FarmBot credentials in both scripts:

1. Open `weed_detection.py` and replace the placeholders:
```python
SERVER = 'https://my.farm.bot'
EMAIL = <email>      # Replace with your actual email in quotes
PASSWORD = <password>  # Replace with your actual password in quotes
```

2. Open `irrigation.py` and make the same changes:
```python
SERVER = 'https://my.farm.bot'
EMAIL = <email>      # Replace with your actual email in quotes
PASSWORD = <password>  # Replace with your actual password in quotes
```

### Key Parameters
- `WEED_RADIUS`: Minimum distance to consider as a crop (default: 50)
- `MAX_DISTANCE`: Maximum distance for weed detection (default: 300)
- `Y_TOLERANCE`: Tolerance for row-based scanning (default: 2)

## Usage

### Running Weed Detection

To run the weed detection system:
```bash
python weed_detection.py
```

This will:
- Move the FarmBot to each plant location
- Take photos and analyze them for weeds
- Mark detected weeds in the FarmBot system
- Clean up old weed records as needed

### Running Irrigation

To run the irrigation system:
```bash
python irrigation.py
```

This will:
- Move the FarmBot to each plant location
- Check soil moisture levels
- Water plants if moisture is below threshold (10%)
- Coordinate movement in an efficient zigzag pattern

## Dependencies

Install required dependencies:
```bash
pip install -r requirements.txt
```

Key dependencies include:
- farmbot: FarmBot Python API
- opencv-python: Computer vision for weed detection
- numpy: Numerical calculations
- requests: API communication
- rich: Enhanced console output
- PIL/Pillow: Image processing

## Notes

- The system uses a zigzag pattern for efficient movement between plants
- Weed detection uses color-based segmentation with OpenCV
- Soil moisture monitoring triggers irrigation when levels fall below 10%
- The system maintains a history of detected weeds and automatically manages storage limits
- Authentication tokens are stored in `farmbot_authorization_token.json` after the first run 