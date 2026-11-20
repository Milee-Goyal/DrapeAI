import os
import cv2
import numpy as np

static_dir = r"D:\Project 1 SEM 7\static"
os.makedirs(static_dir, exist_ok=True)
out_path = os.path.join(static_dir, "default_user.jpg")

# Create a clean, elegant, modern fashion silhouette placeholder
img = np.ones((900, 700, 3), dtype=np.uint8) * 248

# Soft gradient background
for y in range(900):
    val = int(248 - (y / 900.0) * 15)
    img[y, :] = (val, val, val)

# Center of mannequin
cx, cy = 350, 240

# Head contour (soft neutral tone)
cv2.ellipse(img, (cx, cy), (85, 115), 0, 0, 360, (215, 205, 195), -1)
# Neck
cv2.rectangle(img, (cx - 30, cy + 90), (cx + 30, cy + 180), (200, 190, 180), -1)
# Shoulders & Torso
torso_pts = np.array([
    [cx - 30, cy + 170],
    [cx - 180, cy + 240],
    [cx - 160, 900],
    [cx + 160, 900],
    [cx + 180, cy + 240],
    [cx + 30, cy + 170]
], np.int32)
cv2.fillPoly(img, [torso_pts], (180, 170, 160))

# Elegant border
cv2.rectangle(img, (0, 0), (699, 899), (220, 215, 210), 2)
cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"Modern placeholder avatar created at {out_path}")
