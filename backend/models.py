import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    outfits = relationship("OutfitRecommendation", back_populates="user")
    saved_looks = relationship("SavedLook", back_populates="user")
    store_accounts = relationship("UserStoreAccount", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    body_type = Column(String(50), default="Rectangle") # Hourglass, Rectangle, Inverted Triangle, Pear, Athletic
    skin_undertone = Column(String(30), default="Neutral") # Warm, Cool, Neutral
    color_season = Column(String(50), default="Universal Neutral") # Warm Spring, Cool Summer, Deep Autumn, Crisp Winter
    ita_angle = Column(Float, nullable=True)
    portrait_url = Column(String(255), nullable=True)
    preferred_stores = Column(String(255), default="Amazon,Myntra,Flipkart")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile")


class UserStoreAccount(Base):
    __tablename__ = "user_store_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_name = Column(String(80), nullable=False) # e.g. Amazon, Myntra, Flipkart, Meesho, Zara, Ajio
    search_url_template = Column(String(255), nullable=True) # Search URL prefix
    badge_color = Column(String(30), default="#102C57")
    is_active = Column(Boolean, default=True) # Whether used during outfit generation
    is_connected = Column(Boolean, default=True)
    account_email = Column(String(120), nullable=True)
    access_token_simulated = Column(String(100), nullable=True)
    connected_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="store_accounts")


class OutfitRecommendation(Base):
    __tablename__ = "outfit_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(80), nullable=False) # Wedding, Corporate Formal, Cocktail Party, Casual, Date Night, Beach
    budget_limit = Column(Float, nullable=False)
    city = Column(String(80), default="Delhi")
    temperature_c = Column(Float, default=26.0)
    weather_condition = Column(String(80), default="Pleasant")
    color_theme = Column(String(100), nullable=True)
    styling_notes = Column(Text, nullable=True)
    tryon_image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="outfits")
    items = relationship("OutfitItem", back_populates="outfit", cascade="all, delete-orphan")


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    id = Column(Integer, primary_key=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfit_recommendations.id"), nullable=False)
    category = Column(String(50), nullable=False) # Topwear, Bottomwear, Footwear, Accessory
    item_name = Column(String(120), nullable=False)
    color_name = Column(String(60), nullable=False)
    color_hex = Column(String(20), nullable=False)
    fabric = Column(String(60), nullable=True)
    style_tip = Column(String(255), nullable=True)

    outfit = relationship("OutfitRecommendation", back_populates="items")
    ecommerce_matches = relationship("ECommerceProduct", back_populates="outfit_item", cascade="all, delete-orphan")


class ECommerceProduct(Base):
    __tablename__ = "ecommerce_products"

    id = Column(Integer, primary_key=True, index=True)
    outfit_item_id = Column(Integer, ForeignKey("outfit_items.id"), nullable=False)
    store_name = Column(String(80), nullable=False)
    product_title = Column(String(255), nullable=False)
    price_inr = Column(Float, nullable=False)
    rating = Column(Float, default=4.3)
    similarity_score = Column(Float, default=0.92) # CLIP cosine similarity
    image_url = Column(String(255), nullable=True)
    product_url = Column(String(255), nullable=False)

    outfit_item = relationship("OutfitItem", back_populates="ecommerce_matches")


class SavedLook(Base):
    __tablename__ = "saved_looks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    outfit_id = Column(Integer, ForeignKey("outfit_recommendations.id"), nullable=False)
    title = Column(String(120), default="Curated Look")
    tryon_preview = Column(String(255), nullable=True)
    total_cost = Column(Float, default=0.0)
    saved_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="saved_looks")
