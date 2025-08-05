import os
import cv2
import re
import numpy as np
from glob import glob

# Settings
photo_dir = "farmbot_photos/Jul15.2025"
output_filename = "stitched_Jul15.2025_rotated45.jpg"
overlap_pixels_x = 50
overlap_pixels_y = 50
rotation_angle = 45  # Degrees

# Regex to extract coordinates
pattern = re.compile(r"coor\.(\d+)\.(\d+)\.(\d+)\.jpg")

# Load and index images
images = []
for path in glob(os.path.join(photo_dir, "coor.*.*.*.jpg")):
    match = pattern.search(os.path.basename(path))
    if match:
        x, y, z = map(int, match.groups())
        images.append({"x": x, "y": y, "path": path})

if not images:
    raise ValueError("❌ No valid images found.")

# Sort for placement: Y descending, X ascending
images.sort(key=lambda im: (-im["y"], im["x"]))

# Load sample image
sample_img = cv2.imread(images[0]["path"])
if sample_img is None:
    raise ValueError("❌ Sample image failed to load.")
img_h, img_w = sample_img.shape[:2]

# Rotate sample image to get rotated dimensions
def rotate_image(img, angle):
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)

    # Get rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculate new size
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Adjust rotation matrix to new center
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    rotated = cv2.warpAffine(img, M, (new_w, new_h))
    return rotated

# Update step sizes to match rotated image size
rotated_sample = rotate_image(sample_img, rotation_angle)
rot_h, rot_w = rotated_sample.shape[:2]
step_x = rot_w - overlap_pixels_x
step_y = rot_h - overlap_pixels_y

# Get grid
xs = sorted(set(im["x"] for im in images))
ys = sorted(set(im["y"] for im in images), reverse=True)
image_map = {(im["x"], im["y"]): im["path"] for im in images}

# Create mosaic canvas
canvas_w = step_x * (len(xs) - 1) + rot_w
canvas_h = step_y * (len(ys) - 1) + rot_h
stitched = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

# Stitch with rotation
for row_idx, y in enumerate(ys):
    for col_idx, x in enumerate(xs):
        path = image_map.get((x, y))
        if path:
            img = cv2.imread(path)
            if img is not None:
                rotated = rotate_image(img, rotation_angle)
                y_start = row_idx * step_y
                x_start = col_idx * step_x
                y_end = y_start + rotated.shape[0]
                x_end = x_start + rotated.shape[1]

                stitched[y_start:y_end, x_start:x_end] = rotated
            else:
                print(f"⚠️ Failed to load image: {path}")
        else:
            print(f"⚠️ Missing image at ({x}, {y})")

# Save result
cv2.imwrite(output_filename, stitched)
print(f"✅ Mosaic with 45° rotated images saved as: {output_filename}")

