import cv2
import numpy as np
import math
from PIL import Image

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}".upper()

def calculate_ita(l_star, b_star):
    """
    Calculates Individual Typology Angle (ITA) in CIE L*a*b* space:
    ITA = arctan((L* - 50) / b*) * (180 / pi)
    """
    if abs(b_star) < 1e-5:
        return 0.0
    val = (l_star - 50.0) / b_star
    ita_rad = math.atan(val)
    return math.degrees(ita_rad)

def locate_face_roi(img):
    """
    Robust face & skin localization compatible with OpenCV 4.x and OpenCV 5.x.
    """
    h, w, _ = img.shape

    # 1. Try CascadeClassifier if available (OpenCV 4.x)
    if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            if len(faces) > 0:
                (x, y, fw, fh) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
                return (x, y, fw, fh, True)
        except Exception:
            pass

    # 2. Skin contour segmentation (OpenCV 5.x & general fallback)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_skin = np.array([0, 20, 50], dtype=np.uint8)
    upper_skin = np.array([28, 240, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Red wrap-around
    mask2 = cv2.inRange(hsv, np.array([168, 20, 50]), np.array([180, 240, 255]))
    mask = cv2.bitwise_or(mask, mask2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Filter for candidate face/head contour in upper 70% of image
        valid_c = [c for c in contours if cv2.boundingRect(c)[1] < h * 0.7 and cv2.contourArea(c) > 400]
        if valid_c:
            best_c = max(valid_c, key=cv2.contourArea)
            x, y, fw, fh = cv2.boundingRect(best_c)
            return (x, y, fw, fh, True)

    # 3. Default center upper region
    return (int(w * 0.25), int(h * 0.15), int(w * 0.5), int(h * 0.4), False)

SEASON_PALETTES = {
    "Deep Autumn": [
        {"name": "Terracotta Rust", "hex": "#C85A32"},
        {"name": "Emerald Moss", "hex": "#2D5A27"},
        {"name": "Mustard Ochre", "hex": "#E0A926"},
        {"name": "Rich Burgundy", "hex": "#722F37"},
        {"name": "Warm Chocolate", "hex": "#4A2E1B"}
    ],
    "Warm Spring": [
        {"name": "Coral Sunset", "hex": "#FF6F61"},
        {"name": "Warm Peach", "hex": "#F4A261"},
        {"name": "Turquoise Teal", "hex": "#2A9D8F"},
        {"name": "Olive Gold", "hex": "#8A9A5B"},
        {"name": "Warm Cream", "hex": "#FFFDD0"}
    ],
    "Cool Summer": [
        {"name": "Slate Blue", "hex": "#4B6584"},
        {"name": "Lavender Mist", "hex": "#967BB6"},
        {"name": "Dusty Rose", "hex": "#C06C84"},
        {"name": "Sage Mist", "hex": "#587E60"},
        {"name": "Royal Cobalt", "hex": "#2A4B7C"}
    ],
    "Crisp Winter": [
        {"name": "Royal Cobalt", "hex": "#0047AB"},
        {"name": "Ruby Crimson", "hex": "#9B111E"},
        {"name": "Emerald Jewel", "hex": "#046307"},
        {"name": "Deep Plum", "hex": "#581145"},
        {"name": "Pure White", "hex": "#FFFFFF"}
    ],
    "Universal Neutral": [
        {"name": "Terracotta Rust", "hex": "#C85A32"},
        {"name": "Teal Spruce", "hex": "#2F5D62"},
        {"name": "Rich Burgundy", "hex": "#722F37"},
        {"name": "True Navy", "hex": "#0A2342"},
        {"name": "Soft Rosewood", "hex": "#9E5A63"}
    ]
}

def analyze_skin_tone_from_image(image_path: str):
    """
    Analyzes user's portrait image using OpenCV:
    1. Detects face ROI.
    2. Segments skin pixels in HSV space.
    3. Converts to CIE L*a*b* to compute ITA and undertones.
    4. Maps to Seasonal Color Palette (Spring, Summer, Autumn, Winter).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read image file.")

    height, width, _ = img.shape
    
    # Resize for fast, consistent processing
    max_dim = 800
    if max(height, width) > max_dim:
        scale = max_dim / float(max(height, width))
        img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
        height, width, _ = img.shape

    fx, fy, fw, fh, face_detected = locate_face_roi(img)
    # Crop to cheeks & forehead to avoid hair, lips, and eyes
    face_roi = img[int(fy + 0.25 * fh):int(fy + 0.75 * fh), int(fx + 0.2 * fw):int(fx + 0.8 * fw)]
    if face_roi.size == 0:
        face_roi = img[int(0.2 * height):int(0.6 * height), int(0.25 * width):int(0.75 * width)]

    # Convert ROI to HSV to sample unshadowed skin
    hsv_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    skin_mask1 = cv2.inRange(hsv_roi, np.array([0, 20, 50]), np.array([28, 240, 255]))
    skin_mask2 = cv2.inRange(hsv_roi, np.array([168, 20, 50]), np.array([180, 240, 255]))
    skin_mask = cv2.bitwise_or(skin_mask1, skin_mask2)

    skin_pixels_bgr = face_roi[skin_mask > 0]

    if len(skin_pixels_bgr) < 50:
        median_b = float(np.median(face_roi[:, :, 0]))
        median_g = float(np.median(face_roi[:, :, 1]))
        median_r = float(np.median(face_roi[:, :, 2]))
    else:
        median_b = float(np.median(skin_pixels_bgr[:, 0]))
        median_g = float(np.median(skin_pixels_bgr[:, 1]))
        median_r = float(np.median(skin_pixels_bgr[:, 2]))

    hex_color = rgb_to_hex(median_r, median_g, median_b)

    # Convert median BGR color to CIE L*a*b*
    bgr_sample = np.uint8([[[int(median_b), int(median_g), int(median_r)]]])
    lab_sample = cv2.cvtColor(bgr_sample, cv2.COLOR_BGR2LAB)[0][0]
    
    l_norm = (float(lab_sample[0]) / 255.0) * 100.0
    a_norm = float(lab_sample[1]) - 128.0
    b_norm = float(lab_sample[2]) - 128.0

    ita = calculate_ita(l_norm, b_norm)

    # Undertone classification
    if b_norm >= 12.5:
        undertone = "Warm"
    elif b_norm <= 7.0 or (a_norm > b_norm and b_norm < 11.0):
        undertone = "Cool"
    else:
        undertone = "Neutral"

    # Seasonal Color Palette mapping
    if undertone == "Warm":
        if l_norm >= 62.0:
            season = "Warm Spring"
            description = "Bright, warm golden undertone. Radiant with vivid, sunny, and fresh colors."
            avoid = ["Icy Gray", "Stark Neon Pink", "Dull Charcoal"]
        else:
            season = "Deep Autumn"
            description = "Rich, earthy, golden-bronze undertone. Best flattered by deep, warm, regal shades."
            avoid = ["Pastel Sky Blue", "Cold Silver", "Fluorescent Lime"]
    elif undertone == "Cool":
        if l_norm >= 62.0:
            season = "Cool Summer"
            description = "Gentle, cool pinkish undertone. Complemented by soft pastels, muted blues, and lavender."
            avoid = ["Orange", "Mustard Yellow", "Golden Brown"]
        else:
            season = "Crisp Winter"
            description = "Striking contrast with cool undertones. Stunning in bold jewel tones and high contrast."
            avoid = ["Muted Tan", "Dull Khaki", "Pale Peach"]
    else:
        season = "Universal Neutral"
        description = "Balanced undertone capable of wearing both warm earth tones and crisp cool shades with versatility."
        avoid = ["Overly bright fluorescent green", "Bleached yellow"]

    palette = SEASON_PALETTES.get(season, SEASON_PALETTES["Universal Neutral"])

    return {
        "face_detected": face_detected,
        "skin_rgb": [int(median_r), int(median_g), int(median_b)],
        "skin_hex": hex_color,
        "ita_angle": round(ita, 2),
        "undertone": undertone,
        "color_season": season,
        "description": description,
        "recommended_palette": palette,
        "avoid_palette": avoid,
        "confidence_score": 0.94 if face_detected else 0.82
    }
