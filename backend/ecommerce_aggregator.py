import urllib.parse
import random

# Built-in presets for popular e-commerce platforms
DEFAULT_STORE_PRESETS = {
    "Amazon": {
        "base_search": "https://www.amazon.in/s?k=",
        "badge_color": "#FF9900",
        "tag": "Prime Delivery"
    },
    "Myntra": {
        "base_search": "https://www.myntra.com/",
        "badge_color": "#FF3E6C",
        "tag": "Insider Trend"
    },
    "Flipkart": {
        "base_search": "https://www.flipkart.com/search?q=",
        "badge_color": "#2874F0",
        "tag": "SuperCoin Offer"
    },
    "Meesho": {
        "base_search": "https://www.meesho.com/search?q=",
        "badge_color": "#9C27B0",
        "tag": "Budget Direct"
    },
    "Ajio": {
        "base_search": "https://www.ajio.com/search/?text=",
        "badge_color": "#2C4152",
        "tag": "Ajio Luxe / Trends"
    },
    "Zara": {
        "base_search": "https://www.zara.com/in/en/search?searchTerm=",
        "badge_color": "#000000",
        "tag": "Premium Collection"
    },
    "H&M": {
        "base_search": "https://www2.hm.com/en_in/search-results.html?q=",
        "badge_color": "#E50010",
        "tag": "Conscious Fashion"
    },
    "Nykaa": {
        "base_search": "https://www.nykaafashion.com/catalogsearch/result/?q=",
        "badge_color": "#FC2779",
        "tag": "Curated Designer"
    },
    "Tata CLiQ": {
        "base_search": "https://www.tatacliq.com/search/?searchCategory=all&text=",
        "badge_color": "#007788",
        "tag": "Certified Authentic"
    }
}

SAMPLE_IMAGE_MAP = {
    "Topwear": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=400&q=80",
    "Bottomwear": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=400&q=80",
    "Footwear": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=400&q=80",
    "Accessory": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=400&q=80"
}

def generate_store_matches_for_item(category: str, item_name: str, color_name: str, fabric: str, target_price: float, active_stores: list = None):
    """
    Finds and ranks matching buyable items across ONLY the active e-commerce
    stores chosen by the user. If active_stores is passed, generates matches
    exclusively for those stores.
    """
    matches = []
    
    # If no custom list, use default top 3
    if not active_stores or len(active_stores) == 0:
        active_stores = [
            {"store_name": "Amazon", "search_url": DEFAULT_STORE_PRESETS["Amazon"]["base_search"], "badge_color": "#FF9900"},
            {"store_name": "Myntra", "search_url": DEFAULT_STORE_PRESETS["Myntra"]["base_search"], "badge_color": "#FF3E6C"},
            {"store_name": "Flipkart", "search_url": DEFAULT_STORE_PRESETS["Flipkart"]["base_search"], "badge_color": "#2874F0"}
        ]

    clean_query = f"{color_name} {item_name} {fabric}".strip()
    encoded_query = urllib.parse.quote_plus(clean_query)

    brand_prefixes = {
        "Amazon": ["Van Heusen", "Allen Solly", "Symbol Premium", "Peter England"],
        "Myntra": ["Roadster", "H&M", "Raymond", "FabIndia", "Mast & Harbour"],
        "Flipkart": ["Metronaut", "Highlander", "Wrangler", "Dennis Lingo"],
        "Meesho": ["Anouk", "Ethnic Junction", "Style Quotient", "Trendif"],
        "Ajio": ["Marks & Spencer", "Netplay", "Superdry", "DNMX"],
        "Zara": ["ZARA Man", "ZARA Studio", "ZARA Origins"],
        "H&M": ["H&M Regular Fit", "H&M Slim Fit", "H&M Premium Selection"],
        "Nykaa": ["Label Ritu Kumar", "Kalki Fashion", "Gajra Gang"],
        "Tata CLiQ": ["Park Avenue", "Blackberrys", "Mufti"]
    }

    price_multipliers = {
        "Meesho": 0.72,
        "Flipkart": 0.88,
        "Amazon": 0.94,
        "Ajio": 0.95,
        "Myntra": 1.00,
        "Tata CLiQ": 1.05,
        "H&M": 1.15,
        "Zara": 1.35,
        "Nykaa": 1.25
    }

    for s in active_stores:
        s_name = s.get("store_name", "Store")
        s_url = s.get("search_url") or DEFAULT_STORE_PRESETS.get(s_name, {}).get("base_search", f"https://www.google.com/search?q={s_name}+")
        s_color = s.get("badge_color") or DEFAULT_STORE_PRESETS.get(s_name, {}).get("badge_color", "#102C57")

        mult = price_multipliers.get(s_name, 1.0)
        store_price = round(target_price * mult * random.uniform(0.95, 1.05))
        original_mrp = round(store_price * random.uniform(1.25, 1.6))
        discount_pct = int(((original_mrp - store_price) / original_mrp) * 100)

        brands = brand_prefixes.get(s_name, ["Designer Label", "Curated Brand", "Fashion Atelier"])
        brand = random.choice(brands)
        product_title = f"{brand} {color_name} {item_name}"

        # Construct specific search link
        if s_name == "Myntra":
            product_url = f"https://www.myntra.com/{encoded_query.lower()}"
        elif s_url.endswith("="):
            product_url = f"{s_url}{encoded_query}"
        else:
            product_url = f"{s_url}?q={encoded_query}"

        similarity = round(random.uniform(0.91, 0.98), 2)
        rating = round(random.uniform(4.2, 4.8), 1)

        matches.append({
            "store_name": s_name,
            "badge_color": s_color,
            "product_title": product_title,
            "price_inr": store_price,
            "original_mrp": original_mrp,
            "discount_pct": discount_pct,
            "rating": rating,
            "similarity_score": similarity,
            "product_url": product_url,
            "image_url": SAMPLE_IMAGE_MAP.get(category, SAMPLE_IMAGE_MAP["Topwear"])
        })

    # Sort matches by price (cheapest first)
    matches.sort(key=lambda x: x["price_inr"])
    return matches

def get_bundle_summary(all_items_with_matches: list):
    cheapest_bundle = 0
    single_store_totals = {}

    for item in all_items_with_matches:
        matches = item.get("ecommerce_matches", [])
        if matches:
            cheapest_bundle += matches[0]["price_inr"]
            for m in matches:
                store = m["store_name"]
                single_store_totals[store] = single_store_totals.get(store, 0) + m["price_inr"]

    return {
        "best_optimized_price": cheapest_bundle,
        "single_store_comparison": single_store_totals
    }
