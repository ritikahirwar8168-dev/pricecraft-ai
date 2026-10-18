"""
PriceCraft AI - Synthetic Historical Resale Data Generator for TabPFN Foundation Model

This module provides realistic tabular datasets of actual historical resale listings across
eBay, Etsy, and Poshmark. Used by TabPFN to predict optimal pricing, liquidate-speed floors,
and 14-day sale probabilities with zero-shot tabular in-context learning.
"""

import pandas as pd
import numpy as np

# Feature definitions for resale valuation:
# - category_idx: encoded category (0: Streetwear, 1: Electronics, 2: Collectibles, 3: Luxury)
# - condition_score: 1.0 (for parts/damaged) to 10.0 (brand new in box / deadstock)
# - brand_tier: 1 (budget/unbranded), 2 (mid-tier/mall brand), 3 (hype/sought-after), 4 (luxury/grail)
# - rarity_score: 1 (mass produced) to 5 (ultra rare / limited edition)
# - original_retail_usd: approximate original MSRP
# - shipping_included: 1 if free shipping, 0 if buyer pays shipping
# - days_since_release_years: age/vintage factor (in years)
# - demand_trend_score: 1 (cold/declining) to 5 (viral/high search surge)
# Target: sold_price_usd (regression) and sold_within_14d (classification: 1 or 0)

SAMPLE_TRAINING_RECORDS = [
    # Category 0: Vintage & Streetwear
    {"category": "streetwear", "condition_score": 8.5, "brand_tier": 3, "rarity_score": 4, "original_retail_usd": 85.0, "shipping_included": 1, "age_years": 28.0, "demand_trend": 4.5, "sold_price_usd": 145.0, "sold_within_14d": 1},
    {"category": "streetwear", "condition_score": 7.0, "brand_tier": 2, "rarity_score": 2, "original_retail_usd": 65.0, "shipping_included": 0, "age_years": 15.0, "demand_trend": 3.0, "sold_price_usd": 42.0, "sold_within_14d": 0},
    {"category": "streetwear", "condition_score": 9.5, "brand_tier": 4, "rarity_score": 5, "original_retail_usd": 220.0, "shipping_included": 1, "age_years": 22.0, "demand_trend": 5.0, "sold_price_usd": 380.0, "sold_within_14d": 1},
    {"category": "streetwear", "condition_score": 6.0, "brand_tier": 3, "rarity_score": 3, "original_retail_usd": 90.0, "shipping_included": 0, "age_years": 25.0, "demand_trend": 3.5, "sold_price_usd": 78.0, "sold_within_14d": 1},
    {"category": "streetwear", "condition_score": 5.0, "brand_tier": 1, "rarity_score": 1, "original_retail_usd": 40.0, "shipping_included": 0, "age_years": 8.0, "demand_trend": 2.0, "sold_price_usd": 15.0, "sold_within_14d": 0},
    {"category": "streetwear", "condition_score": 9.0, "brand_tier": 3, "rarity_score": 4, "original_retail_usd": 110.0, "shipping_included": 1, "age_years": 30.0, "demand_trend": 4.0, "sold_price_usd": 175.0, "sold_within_14d": 1},
    {"category": "streetwear", "condition_score": 8.0, "brand_tier": 2, "rarity_score": 2, "original_retail_usd": 70.0, "shipping_included": 1, "age_years": 12.0, "demand_trend": 3.0, "sold_price_usd": 48.0, "sold_within_14d": 1},
    {"category": "streetwear", "condition_score": 7.5, "brand_tier": 4, "rarity_score": 4, "original_retail_usd": 350.0, "shipping_included": 1, "age_years": 18.0, "demand_trend": 4.5, "sold_price_usd": 290.0, "sold_within_14d": 1},

    # Category 1: Electronics & Retro Tech
    {"category": "electronics", "condition_score": 9.0, "brand_tier": 3, "rarity_score": 2, "original_retail_usd": 349.0, "shipping_included": 1, "age_years": 3.0, "demand_trend": 4.5, "sold_price_usd": 185.0, "sold_within_14d": 1},
    {"category": "electronics", "condition_score": 6.5, "brand_tier": 2, "rarity_score": 1, "original_retail_usd": 199.0, "shipping_included": 0, "age_years": 4.0, "demand_trend": 2.5, "sold_price_usd": 65.0, "sold_within_14d": 0},
    {"category": "electronics", "condition_score": 8.0, "brand_tier": 4, "rarity_score": 4, "original_retail_usd": 180.0, "shipping_included": 1, "age_years": 24.0, "demand_trend": 4.8, "sold_price_usd": 140.0, "sold_within_14d": 1},
    {"category": "electronics", "condition_score": 9.5, "brand_tier": 3, "rarity_score": 3, "original_retail_usd": 299.0, "shipping_included": 1, "age_years": 2.0, "demand_trend": 4.0, "sold_price_usd": 210.0, "sold_within_14d": 1},
    {"category": "electronics", "condition_score": 4.0, "brand_tier": 2, "rarity_score": 1, "original_retail_usd": 150.0, "shipping_included": 0, "age_years": 6.0, "demand_trend": 1.5, "sold_price_usd": 28.0, "sold_within_14d": 0},
    {"category": "electronics", "condition_score": 8.5, "brand_tier": 4, "rarity_score": 5, "original_retail_usd": 250.0, "shipping_included": 1, "age_years": 20.0, "demand_trend": 5.0, "sold_price_usd": 320.0, "sold_within_14d": 1},

    # Category 2: Collectibles & Cards
    {"category": "collectibles", "condition_score": 9.5, "brand_tier": 4, "rarity_score": 5, "original_retail_usd": 15.0, "shipping_included": 1, "age_years": 26.0, "demand_trend": 5.0, "sold_price_usd": 450.0, "sold_within_14d": 1},
    {"category": "collectibles", "condition_score": 7.0, "brand_tier": 3, "rarity_score": 3, "original_retail_usd": 25.0, "shipping_included": 0, "age_years": 10.0, "demand_trend": 3.0, "sold_price_usd": 45.0, "sold_within_14d": 0},
    {"category": "collectibles", "condition_score": 8.0, "brand_tier": 4, "rarity_score": 4, "original_retail_usd": 30.0, "shipping_included": 1, "age_years": 15.0, "demand_trend": 4.2, "sold_price_usd": 160.0, "sold_within_14d": 1},
    {"category": "collectibles", "condition_score": 5.5, "brand_tier": 2, "rarity_score": 2, "original_retail_usd": 20.0, "shipping_included": 0, "age_years": 5.0, "demand_trend": 2.0, "sold_price_usd": 18.0, "sold_within_14d": 0},

    # Category 3: Luxury & Watches
    {"category": "luxury", "condition_score": 9.0, "brand_tier": 4, "rarity_score": 4, "original_retail_usd": 650.0, "shipping_included": 1, "age_years": 14.0, "demand_trend": 4.6, "sold_price_usd": 520.0, "sold_within_14d": 1},
    {"category": "luxury", "condition_score": 8.0, "brand_tier": 3, "rarity_score": 3, "original_retail_usd": 420.0, "shipping_included": 1, "age_years": 8.0, "demand_trend": 3.8, "sold_price_usd": 260.0, "sold_within_14d": 1},
    {"category": "luxury", "condition_score": 6.5, "brand_tier": 4, "rarity_score": 3, "original_retail_usd": 850.0, "shipping_included": 0, "age_years": 20.0, "demand_trend": 3.5, "sold_price_usd": 380.0, "sold_within_14d": 0},
    {"category": "luxury", "condition_score": 9.8, "brand_tier": 4, "rarity_score": 5, "original_retail_usd": 1200.0, "shipping_included": 1, "age_years": 6.0, "demand_trend": 4.9, "sold_price_usd": 1050.0, "sold_within_14d": 1},
]

CATEGORY_MAP = {
    "streetwear": 0,
    "vintage": 0,
    "clothing": 0,
    "electronics": 1,
    "tech": 1,
    "gaming": 1,
    "collectibles": 2,
    "toys": 2,
    "cards": 2,
    "luxury": 3,
    "watches": 3,
    "jewelry": 3,
}

FEATURE_COLS = [
    "category_code",
    "condition_score",
    "brand_tier",
    "rarity_score",
    "original_retail_usd",
    "shipping_included",
    "age_years",
    "demand_trend",
]

def get_training_dataframe():
    """Returns the processed training dataset ready for TabPFN fitting."""
    df = pd.DataFrame(SAMPLE_TRAINING_RECORDS)
    df["category_code"] = df["category"].map(lambda x: CATEGORY_MAP.get(x.lower(), 0))
    return df

def encode_item_features(item_dict):
    """
    Encodes an incoming item request dictionary into a feature vector
    matching FEATURE_COLS for TabPFN inference.
    """
    category_raw = str(item_dict.get("category", "streetwear")).lower()
    cat_code = CATEGORY_MAP.get(category_raw, 0)

    features = [
        cat_code,
        float(item_dict.get("condition_score", 8.0)),
        float(item_dict.get("brand_tier", 3.0)),
        float(item_dict.get("rarity_score", 3.0)),
        float(item_dict.get("original_retail_usd", 100.0)),
        1.0 if item_dict.get("shipping_included", True) else 0.0,
        float(item_dict.get("age_years", 5.0)),
        float(item_dict.get("demand_trend", 3.5)),
    ]
    return np.array([features])
