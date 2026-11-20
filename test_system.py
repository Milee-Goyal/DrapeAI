import os
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, r"D:\Project 1 SEM 7")

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def run_tests():
    print("[*] Running DrapeAI System Tests (UI Overhaul, Custom Stores & VTON Fix)...")

    # 1. Root Route
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    print("  [+] [1/8] Frontend UI Route OK")

    # 2. Auth: Register / Login
    reg_payload = {
        "username": "fashion_tester_99",
        "email": "tester99@drapeai.com",
        "password": "Password@123"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    if res.status_code == 400 and "already registered" in res.text:
        login_res = client.post("/api/auth/login", json={"username": "fashion_tester_99", "password": "Password@123"})
        token = login_res.json()["access_token"]
    else:
        assert res.status_code == 200, f"Register failed: {res.text}"
        token = res.json()["access_token"]
    print("  [+] [2/8] JWT Auth & Private Session OK")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Custom Stores Management: List, Add, Toggle, Remove
    res = client.get("/api/stores", headers=headers)
    assert res.status_code == 200
    initial_stores = res.json()["stores"]
    print(f"  [+] [3/8] Custom Stores List OK: User has {len(initial_stores)} default stores")

    # Add a new custom store (e.g., Meesho)
    add_store_res = client.post(
        "/api/stores/add",
        headers=headers,
        json={"store_name": "Meesho", "search_url_template": "https://www.meesho.com/search?q=", "badge_color": "#9C27B0"}
    )
    assert add_store_res.status_code == 200
    added_store = add_store_res.json()["store"]
    store_id = added_store["id"]
    print("        -> Added custom store: Meesho")

    # Toggle store
    toggle_res = client.put(f"/api/stores/{store_id}/toggle", headers=headers)
    assert toggle_res.status_code == 200
    # Toggle back to active
    client.put(f"/api/stores/{store_id}/toggle", headers=headers)
    print("        -> Toggled store active state successfully")

    # 4. Portrait Upload & OpenCV Colorimetry
    sample_img = r"D:\Project 1 SEM 7\static\default_user.jpg"
    with open(sample_img, "rb") as f:
        res = client.post(
            "/api/profile/upload-portrait",
            headers=headers,
            files={"file": ("default_user.jpg", f, "image/jpeg")}
        )
    assert res.status_code == 200
    colorimetry = res.json()["colorimetry"]
    print(f"  [+] [4/8] OpenCV Skin Undertone OK: {colorimetry['undertone']} ({colorimetry['color_season']})")

    # 5. Context-Aware Styling & Bounded Budget
    style_payload = {
        "event_type": "Corporate Formal",
        "budget_limit": 5500.0,
        "city": "Mumbai",
        "temperature_c": 31.0,
        "weather_condition": "Warm Humid"
    }
    res = client.post("/api/stylist/generate", headers=headers, json=style_payload)
    assert res.status_code == 200
    outfit = res.json()
    outfit_id = outfit["outfit_id"]
    print(f"  [+] [5/8] AI Stylist OK: '{outfit['theme']}' formulated with {len(outfit['items'])} garments")

    # Verify that the custom store (Meesho) appears in matches because it was added
    all_matched_stores = set()
    for it in outfit["items"]:
        for m in it["ecommerce_matches"]:
            all_matched_stores.add(m["store_name"])
    print(f"        -> Product matches populated for active user stores: {all_matched_stores}")
    assert "Meesho" in all_matched_stores

    # 6. Virtual Try-On (VTON) Photorealistic Draping
    res = client.post(f"/api/tryon/render/{outfit_id}", headers=headers)
    assert res.status_code == 200, f"Try-on failed: {res.text}"
    tryon_data = res.json()
    assert "tryon_image_url" in tryon_data
    tryon_file_path = os.path.join(r"D:\Project 1 SEM 7", tryon_data["tryon_image_url"].lstrip("/"))
    assert os.path.exists(tryon_file_path)
    assert os.path.getsize(tryon_file_path) > 20000
    print(f"  [+] [6/8] Virtual Try-On Engine OK: Garment rendered at {tryon_data['tryon_image_url']}")

    # 6b. Live Garment Color Switcher Test
    recolor_res = client.post(
        f"/api/tryon/recolor/{outfit_id}",
        headers=headers,
        json={"color_hex": "#C85A32", "color_name": "Terracotta Rust"}
    )
    assert recolor_res.status_code == 200, f"Recolor failed: {recolor_res.text}"
    recolor_data = recolor_res.json()
    assert os.path.exists(os.path.join(r"D:\Project 1 SEM 7", recolor_data["tryon_image_url"].lstrip("/")))
    print(f"        -> Live Garment Color Switcher OK: Recolor to Terracotta Rust verified")

    # 7. E-Commerce Cart Sync
    res = client.post(f"/api/ecommerce/sync-bundle/{outfit_id}?store_name=Meesho", headers=headers)
    assert res.status_code == 200
    sync_data = res.json()
    print(f"  [+] [7/8] E-Commerce Cart Sync OK: {sync_data['message']}")

    # 8. Save & Retrieve Private Wardrobe
    res = client.post("/api/wardrobe/save", headers=headers, json={"outfit_id": outfit_id, "title": "Corporate Executive"})
    assert res.status_code == 200
    
    looks_res = client.get("/api/wardrobe/my-looks", headers=headers)
    assert looks_res.status_code == 200
    assert len(looks_res.json()["saved_looks"]) >= 1
    print("  [+] [8/8] Private Wardrobe Saved & Retrieved OK")

    print("\n[SUCCESS] ALL 8 CORE MODULE TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_tests()
