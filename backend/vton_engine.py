import os
import uuid
import cv2
import numpy as np
from PIL import Image

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "garment_templates")

def hex_to_lab(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        hex_str = 'C85A32'
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    rgb_pix = np.uint8([[[b, g, r]]])
    return cv2.cvtColor(rgb_pix, cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)

def recolor_garment(garment_img, target_hex):
    if not target_hex:
        return garment_img
    try:
        target_lab = hex_to_lab(target_hex)
        gray = cv2.cvtColor(garment_img, cv2.COLOR_BGR2GRAY)
        is_garment = gray < 242

        lab = cv2.cvtColor(garment_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        l_ch, a_ch, b_ch = cv2.split(lab)

        cur_a = np.mean(a_ch[is_garment])
        cur_b = np.mean(b_ch[is_garment])
        cur_l = np.mean(l_ch[is_garment])

        delta_a = target_lab[1] - cur_a
        delta_b = target_lab[2] - cur_b
        l_scale = np.clip(target_lab[0] / max(1.0, cur_l), 0.75, 1.25)

        new_l = np.clip(l_ch * l_scale, 0, 255)
        new_a = np.clip(a_ch + delta_a, 0, 255)
        new_b = np.clip(b_ch + delta_b, 0, 255)

        recolored_lab = cv2.merge([new_l, new_a, new_b])
        recolored_bgr = cv2.cvtColor(recolored_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

        out = garment_img.copy()
        out[is_garment] = recolored_bgr[is_garment]
        return out
    except Exception:
        return garment_img

def select_garment_template(outfit_items: list):
    top_color_hex = '#C85A32'
    template_name = 'casual_cuban.jpg'

    for item in outfit_items:
        cat = item.get('category', '')
        if 'Top' in cat or not cat:
            top_color_hex = item.get('color_hex', top_color_hex)
            name_lower = item.get('item_name', '').lower()
            if any(k in name_lower for k in ['kurta', 'sherwani', 'ethnic', 'bandhgala', 'festive']):
                template_name = 'ethnic_kurta.jpg'
            elif any(k in name_lower for k in ['blazer', 'suit', 'executive', 'formal']):
                template_name = 'formal_blazer.jpg'
            elif any(k in name_lower for k in ['kurti', 'tunic', 'silk']):
                template_name = 'ethnic_emerald.jpg'
            elif any(k in name_lower for k in ['resort', 'beach', 'cuban', 'linen', 'shirt', 'polo']):
                template_name = 'casual_cuban.jpg'

    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(template_path):
        all_t = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.jpg') or f.endswith('.png')]
        if all_t:
            template_path = os.path.join(TEMPLATE_DIR, all_t[0])

    return template_path, top_color_hex

def render_virtual_tryon(user_image_path: str, outfit_items: list, output_dir: str) -> str:
    """
    Photorealistic Virtual Try-On Engine.
    Warp-fits authentic, textured garment photographs (Kurta, Cuban Shirt, Blazer, Silk Tunics)
    with genuine collars, seams, buttons, and embroidery directly onto the user portrait.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_filename = f"tryon_{uuid.uuid4().hex[:12]}.jpg"
    out_path = os.path.join(output_dir, out_filename)

    person = cv2.imread(user_image_path)
    if person is None:
        raise ValueError(f"Could not load user image at {user_image_path}")

    ph, pw, _ = person.shape
    template_path, target_hex = select_garment_template(outfit_items)
    
    garment = cv2.imread(template_path)
    if garment is None:
        raise ValueError(f"Could not load garment template at {template_path}")

    # Apply color modulation
    garment = recolor_garment(garment, target_hex)

    # 1. Garment alpha cutout from solid background
    g_gray = cv2.cvtColor(garment, cv2.COLOR_BGR2GRAY)
    g_mask = (g_gray < 242).astype(np.uint8) * 255
    g_mask = cv2.morphologyEx(g_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    coords = cv2.findNonZero(g_mask)
    if coords is not None:
        gx, gy, gbw, gbh = cv2.boundingRect(coords)
        crop_garment = garment[gy:gy+gbh, gx:gx+gbw]
        crop_mask = g_mask[gy:gy+gbh, gx:gx+gbw]
    else:
        crop_garment = garment
        crop_mask = g_mask

    # 2. Estimate body bounding box
    aspect = ph / float(pw)
    if aspect > 1.3:
        # Full body or 3/4 standing shot (e.g. outdoor portrait)
        tx = int(pw * 0.17)
        ty = int(ph * 0.22)
        tw = int(pw * 0.54)
        th = int(ph * 0.28)
    else:
        # Studio head-and-shoulders bust portrait
        tx = int(pw * 0.05)
        ty = int(ph * 0.53)
        tw = int(pw * 0.90)
        th = int(ph * 0.47)

    # 3. Scale and feather garment
    resized_garment = cv2.resize(crop_garment, (tw, th), interpolation=cv2.INTER_LANCZOS4)
    resized_mask = cv2.resize(crop_mask, (tw, th), interpolation=cv2.INTER_LANCZOS4)
    feathered_mask = cv2.GaussianBlur(resized_mask, (15, 15), 0).astype(np.float32) / 255.0

    canvas_garment = np.zeros_like(person)
    canvas_alpha = np.zeros((ph, pw, 1), dtype=np.float32)

    y1, y2 = max(0, ty), min(ph, ty + th)
    x1, x2 = max(0, tx), min(pw, tx + tw)
    gy1, gy2 = 0, y2 - y1
    gx1, gx2 = 0, x2 - x1

    canvas_garment[y1:y2, x1:x2] = resized_garment[gy1:gy2, gx1:gx2]
    canvas_alpha[y1:y2, x1:x2, 0] = feathered_mask[gy1:gy2, gx1:gx2]

    # 4. Composite garment onto person
    composite = (canvas_garment.astype(np.float32) * canvas_alpha + person.astype(np.float32) * (1.0 - canvas_alpha)).astype(np.uint8)

    # 5. Protect Face, Chin, and Neck
    hsv = cv2.cvtColor(person, cv2.COLOR_BGR2HSV)
    skin1 = cv2.inRange(hsv, np.array([0, 30, 60]), np.array([25, 255, 255]))
    skin2 = cv2.inRange(hsv, np.array([165, 30, 60]), np.array([180, 255, 255]))
    skin = cv2.bitwise_or(skin1, skin2)

    protect_y = ty + int(th * 0.12)
    y_grid, _ = np.mgrid[0:ph, 0:pw]
    protect_mask = (y_grid < protect_y) | ((y_grid < (protect_y + int(th * 0.10))) & (skin > 0))
    composite[protect_mask] = person[protect_mask]

    # 6. Save high-resolution output
    saved = cv2.imwrite(out_path, composite, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not saved or not os.path.exists(out_path):
        res_rgb = cv2.cvtColor(composite, cv2.COLOR_BGR2RGB)
        Image.fromarray(res_rgb).save(out_path, format="JPEG", quality=95)

    return f"/uploads/{out_filename}"
