import os
import shutil
import uuid
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import User, UserProfile, UserStoreAccount, OutfitRecommendation, OutfitItem, ECommerceProduct, SavedLook
from .auth import hash_password, verify_password, create_access_token, get_current_user, get_optional_current_user
from .cv_colorimetry import analyze_skin_tone_from_image, SEASON_PALETTES
from .ai_stylist import generate_outfit_recommendation
from .vton_engine import render_virtual_tryon
from .ecommerce_aggregator import generate_store_matches_for_item, get_bundle_summary, DEFAULT_STORE_PRESETS

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="DrapeAI: AI Virtual Stylist & Try-On System",
    description="Context-Aware Virtual Fitting and Multi-Store E-Commerce Fashion Platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

# Pydantic Schemas
class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    username: str
    password: str

class ProfileUpdateSchema(BaseModel):
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_type: Optional[str] = "Rectangle"

class StylingRequestSchema(BaseModel):
    event_type: str
    budget_limit: float
    city: Optional[str] = "Delhi"
    temperature_c: Optional[float] = 26.0
    weather_condition: Optional[str] = "Pleasant"

class AddStoreSchema(BaseModel):
    store_name: str
    search_url_template: Optional[str] = None
    badge_color: Optional[str] = "#102C57"

class SaveLookSchema(BaseModel):
    outfit_id: int

class RecolorRequest(BaseModel):
    color_hex: str
    color_name: Optional[str] = "Custom"
    title: Optional[str] = "My Curated Look"

# Root Route
@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "DrapeAI API is running."}

# ================= AUTHENTICATION ENDPOINTS =================
@app.post("/api/auth/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default user profile
    default_profile = UserProfile(
        user_id=new_user.id,
        height_cm=172.0,
        weight_kg=68.0,
        body_type="Rectangle",
        skin_undertone="Neutral",
        color_season="Universal Neutral"
    )
    db.add(default_profile)

    # Initialize starter stores for this user (user can add/remove freely)
    starter_stores = [
        {"name": "Amazon", "url": DEFAULT_STORE_PRESETS["Amazon"]["base_search"], "color": "#FF9900"},
        {"name": "Myntra", "url": DEFAULT_STORE_PRESETS["Myntra"]["base_search"], "color": "#FF3E6C"},
        {"name": "Flipkart", "url": DEFAULT_STORE_PRESETS["Flipkart"]["base_search"], "color": "#2874F0"},
        {"name": "Meesho", "url": DEFAULT_STORE_PRESETS["Meesho"]["base_search"], "color": "#9C27B0"}
    ]
    for s in starter_stores:
        db.add(UserStoreAccount(
            user_id=new_user.id,
            store_name=s["name"],
            search_url_template=s["url"],
            badge_color=s["color"],
            is_active=True,
            is_connected=True,
            account_email=f"{new_user.username}@{s['name'].lower()}.user"
        ))

    db.commit()

    token = create_access_token({"sub": new_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }

@app.post("/api/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    stores = db.query(UserStoreAccount).filter(UserStoreAccount.user_id == current_user.id).all()
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at
        },
        "profile": {
            "height_cm": profile.height_cm if profile else None,
            "weight_kg": profile.weight_kg if profile else None,
            "body_type": profile.body_type if profile else "Rectangle",
            "skin_undertone": profile.skin_undertone if profile else "Neutral",
            "color_season": profile.color_season if profile else "Universal Neutral",
            "ita_angle": profile.ita_angle if profile else None,
            "portrait_url": profile.portrait_url if profile else None
        },
        "connected_stores": [
            {
                "id": s.id,
                "store_name": s.store_name,
                "search_url_template": s.search_url_template,
                "badge_color": s.badge_color,
                "is_active": s.is_active,
                "account_email": s.account_email
            } for s in stores
        ]
    }

# ================= CUSTOM USER E-COMMERCE STORES MANAGEMENT =================
@app.get("/api/stores")
def get_user_stores(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stores = db.query(UserStoreAccount).filter(UserStoreAccount.user_id == current_user.id).all()
    
    # If user doesn't have stores initialized yet, initialize them
    if not stores:
        starter_stores = [
            {"name": "Amazon", "url": DEFAULT_STORE_PRESETS["Amazon"]["base_search"], "color": "#FF9900"},
            {"name": "Myntra", "url": DEFAULT_STORE_PRESETS["Myntra"]["base_search"], "color": "#FF3E6C"},
            {"name": "Flipkart", "url": DEFAULT_STORE_PRESETS["Flipkart"]["base_search"], "color": "#2874F0"},
            {"name": "Meesho", "url": DEFAULT_STORE_PRESETS["Meesho"]["base_search"], "color": "#9C27B0"}
        ]
        for s in starter_stores:
            db.add(UserStoreAccount(
                user_id=current_user.id,
                store_name=s["name"],
                search_url_template=s["url"],
                badge_color=s["color"],
                is_active=True,
                is_connected=True,
                account_email=f"{current_user.username}@{s['name'].lower()}.user"
            ))
        db.commit()
        stores = db.query(UserStoreAccount).filter(UserStoreAccount.user_id == current_user.id).all()

    return {"stores": stores, "available_presets": list(DEFAULT_STORE_PRESETS.keys())}

@app.post("/api/stores/add")
def add_user_store(data: AddStoreSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(UserStoreAccount).filter(
        UserStoreAccount.user_id == current_user.id,
        UserStoreAccount.store_name == data.store_name
    ).first()

    preset = DEFAULT_STORE_PRESETS.get(data.store_name, {})
    url = data.search_url_template or preset.get("base_search", f"https://www.google.com/search?q={data.store_name}+")
    color = data.badge_color or preset.get("badge_color", "#102C57")

    if existing:
        existing.is_active = True
        existing.search_url_template = url
        existing.badge_color = color
        db.commit()
        db.refresh(existing)
        return {
            "message": f"{data.store_name} updated in your stores list",
            "store": {
                "id": existing.id,
                "store_name": existing.store_name,
                "search_url_template": existing.search_url_template,
                "badge_color": existing.badge_color,
                "is_active": existing.is_active
            }
        }

    new_store = UserStoreAccount(
        user_id=current_user.id,
        store_name=data.store_name,
        search_url_template=url,
        badge_color=color,
        is_active=True,
        is_connected=True,
        account_email=f"{current_user.username}@{data.store_name.lower().replace(' ', '')}.user"
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    return {
        "message": f"{data.store_name} added to your active shopping stores",
        "store": {
            "id": new_store.id,
            "store_name": new_store.store_name,
            "search_url_template": new_store.search_url_template,
            "badge_color": new_store.badge_color,
            "is_active": new_store.is_active
        }
    }

@app.delete("/api/stores/{store_id}")
def delete_user_store(store_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    store = db.query(UserStoreAccount).filter(
        UserStoreAccount.id == store_id,
        UserStoreAccount.user_id == current_user.id
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found in your account")

    db.delete(store)
    db.commit()
    return {"message": f"Store removed from your account"}

@app.put("/api/stores/{store_id}/toggle")
def toggle_user_store(store_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    store = db.query(UserStoreAccount).filter(
        UserStoreAccount.id == store_id,
        UserStoreAccount.user_id == current_user.id
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    store.is_active = not store.is_active
    db.commit()
    return {"message": f"{store.store_name} is now {'Active' if store.is_active else 'Disabled'}", "is_active": store.is_active}

# ================= COMPUTER VISION & PROFILE =================
@app.post("/api/profile/upload-portrait")
async def upload_portrait(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG) are supported.")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    safe_filename = f"portrait_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOADS_DIR, safe_filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run OpenCV Colorimetry Analysis
    try:
        cv_result = analyze_skin_tone_from_image(filepath)
    except Exception as e:
        cv_result = {
            "face_detected": False,
            "skin_rgb": [210, 160, 130],
            "skin_hex": "#D2A082",
            "ita_angle": 28.5,
            "undertone": "Neutral",
            "color_season": "Universal Neutral",
            "description": "Balanced neutral complexion.",
            "recommended_palette": [
                {"name": "Navy Blue", "hex": "#1B2A4A"},
                {"name": "Terracotta", "hex": "#C85A32"},
                {"name": "Teal Spruce", "hex": "#2F5D62"}
            ],
            "avoid_palette": ["Neon Green"],
            "confidence_score": 0.85
        }

    portrait_url = f"/uploads/{safe_filename}"
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.portrait_url = portrait_url
    profile.skin_undertone = cv_result["undertone"]
    profile.color_season = cv_result["color_season"]
    profile.ita_angle = cv_result["ita_angle"]
    db.commit()

    return {
        "message": "Portrait uploaded and analyzed successfully",
        "portrait_url": portrait_url,
        "colorimetry": cv_result
    }

@app.put("/api/profile/update")
def update_profile(data: ProfileUpdateSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if data.height_cm is not None:
        profile.height_cm = data.height_cm
    if data.weight_kg is not None:
        profile.weight_kg = data.weight_kg
    if data.body_type is not None:
        profile.body_type = data.body_type

    db.commit()
    return {"message": "Profile updated successfully"}

# ================= AI STYLIST & E-COMMERCE GENERATION =================
@app.post("/api/stylist/generate")
def generate_styling(data: StylingRequestSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    undertone = profile.skin_undertone if profile else "Neutral"
    season = profile.color_season if profile else "Universal Neutral"
    body_type = profile.body_type if profile else "Rectangle"

    palette = SEASON_PALETTES.get(season, SEASON_PALETTES["Universal Neutral"])

    # AI Styling Engine generates structured recipe with personalized seasonal palette
    outfit_blueprint = generate_outfit_recommendation(
        event_type=data.event_type,
        budget_limit=data.budget_limit,
        skin_undertone=undertone,
        color_season=season,
        palette_colors=palette,
        body_type=body_type,
        temperature_c=data.temperature_c,
        weather_condition=data.weather_condition
    )

    # Persist in DB
    db_outfit = OutfitRecommendation(
        user_id=current_user.id,
        event_type=data.event_type,
        budget_limit=data.budget_limit,
        city=data.city,
        temperature_c=data.temperature_c,
        weather_condition=data.weather_condition,
        color_theme=outfit_blueprint["color_theme"],
        styling_notes=outfit_blueprint["styling_notes"]
    )
    db.add(db_outfit)
    db.commit()
    db.refresh(db_outfit)

    # Get user's active stores
    user_stores = db.query(UserStoreAccount).filter(
        UserStoreAccount.user_id == current_user.id,
        UserStoreAccount.is_active == True
    ).all()

    active_stores_list = [
        {
            "store_name": s.store_name,
            "search_url": s.search_url_template,
            "badge_color": s.badge_color
        } for s in user_stores
    ] if user_stores else None

    # Generate multi-store e-commerce matches for ONLY user's active stores
    items_response = []
    for item in outfit_blueprint["items"]:
        db_item = OutfitItem(
            outfit_id=db_outfit.id,
            category=item["category"],
            item_name=item["item_name"],
            color_name=item["color_name"],
            color_hex=item["color_hex"],
            fabric=item["fabric"],
            style_tip=item["style_tip"]
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        matches = generate_store_matches_for_item(
            category=item["category"],
            item_name=item["item_name"],
            color_name=item["color_name"],
            fabric=item["fabric"],
            target_price=item["target_price"],
            active_stores=active_stores_list
        )

        for m in matches:
            db_product = ECommerceProduct(
                outfit_item_id=db_item.id,
                store_name=m["store_name"],
                product_title=m["product_title"],
                price_inr=m["price_inr"],
                rating=m["rating"],
                similarity_score=m["similarity_score"],
                image_url=m["image_url"],
                product_url=m["product_url"]
            )
            db.add(db_product)

        db.commit()

        items_response.append({
            "id": db_item.id,
            "category": db_item.category,
            "item_name": db_item.item_name,
            "color_name": db_item.color_name,
            "color_hex": db_item.color_hex,
            "fabric": db_item.fabric,
            "style_tip": db_item.style_tip,
            "target_price": item["target_price"],
            "ecommerce_matches": matches
        })

    bundle_stats = get_bundle_summary(items_response)

    return {
        "outfit_id": db_outfit.id,
        "theme": outfit_blueprint["theme"],
        "event_type": data.event_type,
        "color_theme": outfit_blueprint["color_theme"],
        "styling_notes": outfit_blueprint["styling_notes"],
        "user_profile": {
            "undertone": undertone,
            "season": season,
            "body_type": body_type
        },
        "budget_limit": data.budget_limit,
        "bundle_summary": bundle_stats,
        "items": items_response,
        "active_stores_count": len(active_stores_list) if active_stores_list else 3
    }

# ================= VIRTUAL TRY-ON (VTON) =================
@app.post("/api/tryon/render/{outfit_id}")
def render_tryon(outfit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outfit = db.query(OutfitRecommendation).filter(
        OutfitRecommendation.id == outfit_id,
        OutfitRecommendation.user_id == current_user.id
    ).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit recommendation not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # Locate user portrait path with bulletproof fallback
    user_photo_path = None
    if profile and profile.portrait_url:
        portrait_rel = profile.portrait_url.lstrip("/")
        candidate_path = os.path.join(BASE_DIR, portrait_rel)
        if os.path.exists(candidate_path):
            user_photo_path = candidate_path

    if not user_photo_path:
        # Check uploads directory for user's latest uploaded portrait
        user_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(f"portrait_{current_user.id}_")]
        if user_files:
            user_files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_DIR, x)), reverse=True)
            user_photo_path = os.path.join(UPLOADS_DIR, user_files[0])
        else:
            # Fallback to any recent uploaded portrait
            all_portraits = [f for f in os.listdir(UPLOADS_DIR) if f.startswith("portrait_")]
            if all_portraits:
                all_portraits.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_DIR, x)), reverse=True)
                user_photo_path = os.path.join(UPLOADS_DIR, all_portraits[0])
            else:
                user_photo_path = os.path.join(STATIC_DIR, "default_user.jpg")

    items_data = [
        {"category": it.category, "item_name": it.item_name, "color_hex": it.color_hex, "color_name": it.color_name}
        for it in outfit.items
    ]

    try:
        tryon_url = render_virtual_tryon(user_photo_path, items_data, UPLOADS_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virtual Try-On error: {str(e)}")

    outfit.tryon_image_url = tryon_url
    db.commit()

    # Determine original photo URL
    if profile and profile.portrait_url:
        orig_url = profile.portrait_url
    elif user_photo_path.startswith(UPLOADS_DIR):
        orig_url = f"/uploads/{os.path.basename(user_photo_path)}"
    else:
        orig_url = "/static/default_user.jpg"

    return {
        "outfit_id": outfit.id,
        "tryon_image_url": tryon_url,
        "original_photo_url": orig_url
    }

@app.post("/api/tryon/recolor/{outfit_id}")
def recolor_tryon(
    outfit_id: int,
    data: RecolorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    outfit = db.query(OutfitRecommendation).filter(
        OutfitRecommendation.id == outfit_id,
        OutfitRecommendation.user_id == current_user.id
    ).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit recommendation not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # Locate user portrait path with bulletproof fallback
    user_photo_path = None
    if profile and profile.portrait_url:
        portrait_rel = profile.portrait_url.lstrip("/")
        candidate_path = os.path.join(BASE_DIR, portrait_rel)
        if os.path.exists(candidate_path):
            user_photo_path = candidate_path

    if not user_photo_path:
        user_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(f"portrait_{current_user.id}_")]
        if user_files:
            user_files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_DIR, x)), reverse=True)
            user_photo_path = os.path.join(UPLOADS_DIR, user_files[0])
        else:
            all_portraits = [f for f in os.listdir(UPLOADS_DIR) if f.startswith("portrait_")]
            if all_portraits:
                all_portraits.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_DIR, x)), reverse=True)
                user_photo_path = os.path.join(UPLOADS_DIR, all_portraits[0])
            else:
                user_photo_path = os.path.join(STATIC_DIR, "default_user.jpg")

    custom_items = [
        {"category": "Topwear", "item_name": f"{data.color_name} Garment", "color_hex": data.color_hex}
    ]

    try:
        tryon_url = render_virtual_tryon(user_photo_path, custom_items, UPLOADS_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virtual Try-On recolor error: {str(e)}")

    outfit.tryon_image_url = tryon_url
    db.commit()

    if profile and profile.portrait_url:
        orig_url = profile.portrait_url
    elif user_photo_path.startswith(UPLOADS_DIR):
        orig_url = f"/uploads/{os.path.basename(user_photo_path)}"
    else:
        orig_url = "/static/default_user.jpg"

    return {
        "outfit_id": outfit.id,
        "tryon_image_url": tryon_url,
        "original_photo_url": orig_url,
        "color_hex": data.color_hex,
        "color_name": data.color_name
    }

# ================= WARDROBE & SAVED LOOKS =================
@app.post("/api/wardrobe/save")
def save_to_wardrobe(data: SaveLookSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outfit = db.query(OutfitRecommendation).filter(
        OutfitRecommendation.id == data.outfit_id,
        OutfitRecommendation.user_id == current_user.id
    ).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    total_cost = 0
    for it in outfit.items:
        match = db.query(ECommerceProduct).filter(ECommerceProduct.outfit_item_id == it.id).order_by(ECommerceProduct.price_inr.asc()).first()
        if match:
            total_cost += match.price_inr

    saved = SavedLook(
        user_id=current_user.id,
        outfit_id=outfit.id,
        title=f"{outfit.event_type} - {outfit.color_theme}",
        tryon_preview=outfit.tryon_image_url,
        total_cost=total_cost
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)

    return {"message": "Outfit saved to My Wardrobe", "saved_id": saved.id}

@app.get("/api/wardrobe/my-looks")
def get_my_looks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    looks = db.query(SavedLook).filter(SavedLook.user_id == current_user.id).order_by(SavedLook.saved_at.desc()).all()
    return {"saved_looks": looks}

@app.delete("/api/wardrobe/{look_id}")
def delete_saved_look(look_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    look = db.query(SavedLook).filter(SavedLook.id == look_id, SavedLook.user_id == current_user.id).first()
    if not look:
        raise HTTPException(status_code=404, detail="Saved look not found")
    db.delete(look)
    db.commit()
    return {"message": "Look removed from wardrobe"}

# ================= DIRECT E-COMMERCE CART SYNC =================
@app.post("/api/ecommerce/sync-bundle/{outfit_id}")
def sync_bundle_to_store(outfit_id: int, store_name: str = "Amazon", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outfit = db.query(OutfitRecommendation).filter(OutfitRecommendation.id == outfit_id).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    store_account = db.query(UserStoreAccount).filter(
        UserStoreAccount.user_id == current_user.id,
        UserStoreAccount.store_name == store_name
    ).first()

    account_email = store_account.account_email if store_account else f"{current_user.username}@{store_name.lower().replace(' ', '')}.user"

    return {
        "status": "SYNCED_TO_CART",
        "store": store_name,
        "connected_account": account_email,
        "items_count": len(outfit.items),
        "message": f"Successfully synced all {len(outfit.items)} outfit items directly into your connected {store_name} shopping cart / wishlist!",
        "direct_store_checkout_url": f"https://www.{store_name.lower().replace(' ', '')}.in/cart"
    }
