# DrapeAI: AI Virtual Stylist & Try-On System

> **An Intelligent Context-Aware Virtual Try-On and Cross-Platform E-Commerce Outfit Recommendation System**  
> *Final Year Major Project (7th Semester) — 100% Non-Java Tech Stack*

---

## Key Features & Updates

1. **Modern Responsive UI:**
   * Clean, modern typography, card layout, and step-by-step workflow.
   * High-contrast Before vs. After Virtual Try-On canvas.
2. **Custom E-Commerce Store Manager (User Controlled):**
   * Users can **Add ANY store** (e.g. Meesho, Flipkart, Nykaa, H&M, or custom URL).
   * Users can **Delete/Remove** any store they do not use.
   * Users can **Enable/Disable** stores with a single toggle.
   * Outfit recommendations query **only the active stores** chosen by the user.
3. **Dedicated User Authentication & Data Isolation:**
   * JWT authentication with `bcrypt` password encryption.
   * Every user has a private profile: their uploaded photo, private custom stores, and saved wardrobe are secure and isolated.
4. **Photorealistic 2D Virtual Try-On (VTON) Fix:**
   * Visible, realistic garment synthesis and draping.
   * Anatomically maps neck, shoulders, and chest.
   * Replaces the user's clothing with the recommended outfit (Blazer, Kurta, Sherwani, Evening Shirt, Polo) in the exact chosen color and texture.
   * Preserves natural lighting via luminance blending.
   * Cache-busting (`?t=...`) ensures the user's browser immediately shows the newly rendered fitting without showing the old image.
5. **OpenCV Skin Undertone & Colorimetry:**
   * Real-time Individual Typology Angle (ITA) in CIE L\*a\*b\* space.
   * Classifies user into Warm, Cool, or Neutral undertones and Seasonal Color Palettes (Spring, Summer, Autumn, Winter).
6. **One-Click Cart Synchronization:**
   * Direct transfer of the entire outfit bundle into the connected Amazon, Flipkart, Myntra, or Meesho cart.

---

## Technology Stack (Zero Java)

| Layer | Technologies |
| :--- | :--- |
| **Frontend UI** | HTML5, CSS3 (Modern Luxury Design), Vanilla JavaScript (ES6+ Fetch API) |
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn (Asynchronous REST API) |
| **Database & ORM** | SQLite, SQLAlchemy ORM |
| **Authentication** | PyJWT, Passlib, Bcrypt |
| **Computer Vision** | OpenCV (`opencv-python`), NumPy, Pillow |
| **AI Stylist & VTON** | Generative Styling Knowledge Graph, 2D Draping Engine, Multi-Store Visual Aggregator |

---

## How to Run the Project (One-Click)

1. Open PowerShell or Command Prompt.
2. Run:
```powershell
cd "D:\Project 1 SEM 7"
python run.py
```
3. The server starts at `http://127.0.0.1:8000` and automatically opens your web browser!

---

## Automated Test Verification

Run the test suite anytime:
```powershell
python test_system.py
```
All 8 integration tests verify:
* Root UI Route
* JWT Authentication
* Custom Stores Management (Add / Toggle / Remove)
* OpenCV Skin Tone Colorimetry
* Context-Aware Styling Bounded by Budget
* Virtual Try-On Photorealistic Inpainting
* E-Commerce Cart Sync
* Private Wardrobe Persistence
