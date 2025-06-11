import cv2
import os

# Path to your images
image_folder = os.path.expanduser('~/Downloads/FarmBotEnV/Farmbot/farmbot_photos')

# Get all jpg images in the folder
image_files = sorted([
    os.path.join(image_folder, f)
    for f in os.listdir(image_folder)
    if f.lower().endswith('.jpg')
])

# Load images
images = [cv2.imread(f) for f in image_files]

# Check for empty or unreadable images
images = [img for img in images if img is not None]

if len(images) < 2:
    print("Need at least two images to create a panorama.")
    exit()

# Create a stitcher object (works for OpenCV 3 and 4)
try:
    stitcher = cv2.Stitcher_create()
except AttributeError:
    stitcher = cv2.createStitcher()

# Stitch the images
status, panorama = stitcher.stitch(images)

if status == cv2.Stitcher_OK:
    output_path = os.path.join(image_folder, 'farmbot_panorama.jpg')
    cv2.imwrite(output_path, panorama)
    print(f"Panorama saved to {output_path}")
else:
    print("Stitching failed. Error code:", status)
