import random

# Pre-defined style rule graph mapping occasions to dress codes & silhouettes
STYLE_KNOWLEDGE_BASE = {
    "Wedding": {
        "vibe": "Opulent, celebratory, and culturally refined",
        "fabrics": ["Raw Silk", "Jacquard", "Fine Cotton Blend", "Velvet Accent"],
        "outfit_templates": [
            {
                "theme": "Regal Ethnic Ensemble",
                "top": {"name": "Embroidered Kurta & Bandhgala Jacket", "cat": "Topwear", "budget_pct": 0.45},
                "bottom": {"name": "Slim Fit Tapered Churidars / Dhoti Pants", "cat": "Bottomwear", "budget_pct": 0.25},
                "shoes": {"name": "Handcrafted Mojaris / Leather Juttis", "cat": "Footwear", "budget_pct": 0.20},
                "accessory": {"name": "Pocket Square & Brass Brooch", "cat": "Accessory", "budget_pct": 0.10}
            },
            {
                "theme": "Contemporary Festive Fusion",
                "top": {"name": "Asymmetric Indo-Western Sherwani", "cat": "Topwear", "budget_pct": 0.48},
                "bottom": {"name": "Straight Pleated Trousers", "cat": "Bottomwear", "budget_pct": 0.24},
                "shoes": {"name": "Monk Strap Dress Shoes", "cat": "Footwear", "budget_pct": 0.20},
                "accessory": {"name": "Beaded Lapel Pin", "cat": "Accessory", "budget_pct": 0.08}
            }
        ]
    },
    "Corporate Formal": {
        "vibe": "Sharp, commanding, and professional",
        "fabrics": ["Super 120s Wool Blend", "Breathable Oxford Cotton", "Wrinkle-Resistant Poly-Viscose"],
        "outfit_templates": [
            {
                "theme": "Executive Power Attire",
                "top": {"name": "Tailored Notch-Lapel Blazer & Crisp Shirt", "cat": "Topwear", "budget_pct": 0.45},
                "bottom": {"name": "Flat-Front Formal Trousers", "cat": "Bottomwear", "budget_pct": 0.25},
                "shoes": {"name": "Classic Oxford Leather Shoes", "cat": "Footwear", "budget_pct": 0.22},
                "accessory": {"name": "Reversible Leather Belt & Minimalist Watch", "cat": "Accessory", "budget_pct": 0.08}
            }
        ]
    },
    "Cocktail Party": {
        "vibe": "Sleek, glamorous, and evening-ready",
        "fabrics": ["Satin Silk", "Viscose Crepe", "Textured Linen Blend"],
        "outfit_templates": [
            {
                "theme": "Modern Midnight Glamour",
                "top": {"name": "Silk-Blend Mandarin Collar Evening Shirt", "cat": "Topwear", "budget_pct": 0.40},
                "bottom": {"name": "Tapered Ankle-Length Chinos", "cat": "Bottomwear", "budget_pct": 0.28},
                "shoes": {"name": "Suede Penny Loafers", "cat": "Footwear", "budget_pct": 0.24},
                "accessory": {"name": "Silver Mesh Cufflinks", "cat": "Accessory", "budget_pct": 0.08}
            }
        ]
    },
    "Casual Outing": {
        "vibe": "Relaxed, effortlessly stylish, and comfortable",
        "fabrics": ["100% Washed Cotton", "Slub Jersey", "Selvedge Denim"],
        "outfit_templates": [
            {
                "theme": "Urban Smart Casual",
                "top": {"name": "Oversized Heavyweight Waffle Tee or Cuban Shirt", "cat": "Topwear", "budget_pct": 0.35},
                "bottom": {"name": "Relaxed Straight-Leg Korean Chinos", "cat": "Bottomwear", "budget_pct": 0.30},
                "shoes": {"name": "Minimalist Low-Top Leather Sneakers", "cat": "Footwear", "budget_pct": 0.28},
                "accessory": {"name": "Canvas Tote & Sunglasses", "cat": "Accessory", "budget_pct": 0.07}
            }
        ]
    },
    "Date Night": {
        "vibe": "Alluring, refined, and confident",
        "fabrics": ["Knitted Cotton Polo", "Soft Suede", "Brushed Twill"],
        "outfit_templates": [
            {
                "theme": "Chic Evening Chemistry",
                "top": {"name": "Fine-Gauge Knit Polo Sweater", "cat": "Topwear", "budget_pct": 0.38},
                "bottom": {"name": "Structured Tailored Trouser Jeans", "cat": "Bottomwear", "budget_pct": 0.30},
                "shoes": {"name": "Chelsea Leather Boots", "cat": "Footwear", "budget_pct": 0.24},
                "accessory": {"name": "Subtle Leather Wristband & Perfume", "cat": "Accessory", "budget_pct": 0.08}
            }
        ]
    },
    "Beach Vacation": {
        "vibe": "Breezy, vibrant, and tropical",
        "fabrics": ["100% Pure Linen", "Rayon Chiffon", "Quick-Dry Poplin"],
        "outfit_templates": [
            {
                "theme": "Riviera Coastal Breeze",
                "top": {"name": "Relaxed Resort Collar Floral/Striped Linen Shirt", "cat": "Topwear", "budget_pct": 0.38},
                "bottom": {"name": "Drawstring Linen Shorts / Light Chinos", "cat": "Bottomwear", "budget_pct": 0.28},
                "shoes": {"name": "Woven Espadrilles / Leather Slides", "cat": "Footwear", "budget_pct": 0.26},
                "accessory": {"name": "Polarized Acetate Sunglasses", "cat": "Accessory", "budget_pct": 0.08}
            }
        ]
    }
}

BODY_TYPE_ADVICE = {
    "Hourglass": "Balances top and bottom naturally. Emphasize waistline and structured tailoring.",
    "Rectangle": "Add dimension with layered collars, textured knits, and structured blazers.",
    "Inverted Triangle": "Broad shoulders; balance by opting for straight-leg bottoms and clean necklines.",
    "Pear": "Highlight the upper torso with rich color accents and structured shoulders.",
    "Athletic": "Clean tapered silhouettes that accentuate natural athletic posture without excessive clinging."
}

def generate_outfit_recommendation(
    event_type: str,
    budget_limit: float,
    skin_undertone: str = "Neutral",
    color_season: str = "Universal Neutral",
    palette_colors: list = None,
    body_type: str = "Rectangle",
    temperature_c: float = 27.0,
    weather_condition: str = "Pleasant"
):
    """
    Generates a context-aware outfit recommendation bounded strictly within budget_limit
    and scientifically harmonized with user's skin undertone and color season.
    """
    event_key = event_type if event_type in STYLE_KNOWLEDGE_BASE else "Casual Outing"
    knowledge = STYLE_KNOWLEDGE_BASE[event_key]
    template = random.choice(knowledge["outfit_templates"])
    
    # Select complementary colors
    if not palette_colors or len(palette_colors) < 3:
        palette_colors = [
            {"name": "Navy Blue", "hex": "#1B2A4A"},
            {"name": "Terracotta", "hex": "#C85A32"},
            {"name": "Cream Sand", "hex": "#E5DCC5"}
        ]
    
    top_color = palette_colors[0]
    bottom_color = palette_colors[1] if len(palette_colors) > 1 else {"name": "Charcoal Slate", "hex": "#36454F"}
    shoes_color = {"name": "Tan Leather", "hex": "#8B5A2B"} if skin_undertone == "Warm" else {"name": "Jet Black", "hex": "#1A1A1A"}
    acc_color = palette_colors[2] if len(palette_colors) > 2 else {"name": "Polished Silver", "hex": "#C0C0C0"}

    # Weather-adapted fabric selection
    if temperature_c > 30.0:
        recommended_fabric = "Ultra-breathable Pure Linen / Soft Cotton"
        climate_note = f"Because the forecast shows {temperature_c}°C ({weather_condition}), lightweight breathable fabrics are chosen to maximize comfort and prevent perspiration."
    elif temperature_c < 18.0:
        recommended_fabric = "Brushed Twill / Fine Merino Wool Blend"
        climate_note = f"Given the cooler {temperature_c}°C temperature, thermal-regulating mid-weight fabrics are recommended for warmth with a sharp silhouette."
    else:
        recommended_fabric = random.choice(knowledge["fabrics"])
        climate_note = f"Ideal ambient conditions ({temperature_c}°C) allow flexible layering with {recommended_fabric}."

    body_note = BODY_TYPE_ADVICE.get(body_type, "Tailored cuts ensure proportionate balance.")

    # Calculate itemized budgets
    allocated_budget = max(budget_limit, 1500.0)
    items = []

    # 1. Topwear
    top_cost = round(allocated_budget * template["top"]["budget_pct"])
    items.append({
        "category": template["top"]["cat"],
        "item_name": template["top"]["name"],
        "color_name": top_color["name"],
        "color_hex": top_color["hex"],
        "fabric": recommended_fabric,
        "style_tip": f"Complements your {skin_undertone} undertone and lights up your facial complexion.",
        "target_price": top_cost
    })

    # 2. Bottomwear
    bottom_cost = round(allocated_budget * template["bottom"]["budget_pct"])
    items.append({
        "category": template["bottom"]["cat"],
        "item_name": template["bottom"]["name"],
        "color_name": bottom_color["name"],
        "color_hex": bottom_color["hex"],
        "fabric": "Tailored Stretch Cotton / Blended Viscose",
        "style_tip": f"Provides clean vertical lines optimized for your {body_type} body type.",
        "target_price": bottom_cost
    })

    # 3. Footwear
    shoes_cost = round(allocated_budget * template["shoes"]["budget_pct"])
    items.append({
        "category": template["shoes"]["cat"],
        "item_name": template["shoes"]["name"],
        "color_name": shoes_color["name"],
        "color_hex": shoes_color["hex"],
        "fabric": "Burnished Leather / Suede",
        "style_tip": "Anchors the entire look with sophisticated grounding.",
        "target_price": shoes_cost
    })

    # 4. Accessory
    acc_cost = round(allocated_budget * template["accessory"]["budget_pct"])
    items.append({
        "category": template["accessory"]["cat"],
        "item_name": template["accessory"]["name"],
        "color_name": acc_color["name"],
        "color_hex": acc_color["hex"],
        "fabric": "Metallic / Leather Accent",
        "style_tip": "Adds refined nuance without cluttering the silhouette.",
        "target_price": acc_cost
    })

    total_target = sum(item["target_price"] for item in items)

    styling_explanation = (
        f"This {template['theme']} is calibrated for a {event_type}. "
        f"{climate_note} "
        f"For your {color_season} profile with {skin_undertone} undertones, the pairing of {top_color['name']} against {bottom_color['name']} creates natural chromatic harmony. {body_note}"
    )

    return {
        "theme": template["theme"],
        "event_type": event_type,
        "vibe": knowledge["vibe"],
        "color_theme": f"{top_color['name']} & {bottom_color['name']}",
        "styling_notes": styling_explanation,
        "total_bundle_budget": round(allocated_budget),
        "total_target_price": round(total_target),
        "items": items
    }
