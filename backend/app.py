"""
PriceCraft AI - FastAPI Application Server
Multi-agent e-commerce resale pricing & listing optimizer built with open-source AI.

Core Engines:
- Prior Labs TabPFN-3.5: Tabular Foundation Model for Zero-Shot Resale Valuation
- Google Gemma 2: Open-Weight Copywriting & SEO Marketplace Generation
- SerpApi: Live Competitor Comps & Market Radar
- ElevenLabs: Neural Voiceover Social Promo Generator
- Sentry: Real-Time Agent Telemetry & Span Tracing
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from .tabpfn_engine import predict_resale_metrics
from .gemma_engine import generate_listing_with_gemma
from .serpapi_engine import fetch_competitor_comps
from .elevenlabs_engine import generate_voiceover_promo
from .sentry_engine import init_sentry, AgentSpan, get_recent_traces
from .inventory_db import init_db, save_item, get_all_items, delete_item, export_inventory_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pricecraft.app")

# Initialize telemetry and database
init_sentry()
init_db()

app = FastAPI(
    title="PriceCraft AI API",
    description="Intelligent Resale Pricing & Copywriting Engine Powered by TabPFN & Google Gemma 2",
    version="1.0.0"
)

# ----------------- Data Models -----------------

class ItemAnalysisRequest(BaseModel):
    title: str = Field(..., example="Vintage 1994 Nike Spellout Windbreaker Jacket")
    brand: str = Field("Nike", example="Nike")
    category: str = Field("streetwear", example="streetwear")
    condition_score: float = Field(8.5, ge=1.0, le=10.0, example=8.5)
    condition_notes: str = Field("Minor signs of gentle wear, all zippers work smoothly, no holes.", example="Clean condition")
    features: str = Field("Nylon shell, colorblock teal & purple, embroidered back spellout logo, size Large", example="Colorblock, Large")
    original_retail_usd: float = Field(85.0, example=85.0)
    purchase_cost: float = Field(15.0, example=15.0)
    brand_tier: float = Field(3.0, ge=1.0, le=4.0, example=3.0)
    rarity_score: float = Field(4.0, ge=1.0, le=5.0, example=4.0)
    age_years: float = Field(28.0, example=28.0)
    demand_trend: float = Field(4.5, ge=1.0, le=5.0, example=4.5)
    shipping_included: bool = Field(True, example=True)

class VoiceoverRequest(BaseModel):
    script: str = Field(..., example="Grail alert: Vintage 1994 Nike Windbreaker just hit our shop. Link in bio!")

class SaveInventoryRequest(BaseModel):
    item_data: Dict[str, Any]
    valuation: Dict[str, Any]
    listing: Dict[str, Any]

# ----------------- Sample Preset Items -----------------

SAMPLE_PRESETS = [
    {
        "id": "vintage_nike",
        "name": "Vintage 1994 Nike Spellout Windbreaker",
        "category_badge": "Vintage Streetwear",
        "data": {
            "title": "Vintage 1994 Nike Spellout Windbreaker Jacket",
            "brand": "Nike",
            "category": "streetwear",
            "condition_score": 8.8,
            "condition_notes": "Excellent vintage condition. Elastic cuffs tight, no cigarette smoke, minor fading on inner collar tag.",
            "features": "Embroidered swoosh, oversized 90s silhouette, colorblock purple/teal, heavy-duty zipper, size XL",
            "original_retail_usd": 85.0,
            "purchase_cost": 12.0,
            "brand_tier": 3.0,
            "rarity_score": 4.0,
            "age_years": 29.0,
            "demand_trend": 4.8,
            "shipping_included": True
        }
    },
    {
        "id": "sony_headphones",
        "name": "Sony WH-1000XM4 Noise Cancelling",
        "category_badge": "Consumer Electronics",
        "data": {
            "title": "Sony WH-1000XM4 Wireless Noise-Cancelling Headphones (Midnight Blue)",
            "brand": "Sony",
            "category": "electronics",
            "condition_score": 9.2,
            "condition_notes": "Like new condition in original hard carrying case with all original audio and charging cables.",
            "features": "Industry-leading active noise cancellation, 30-hour battery life, multipoint Bluetooth pairing, LDAC support",
            "original_retail_usd": 348.0,
            "purchase_cost": 80.0,
            "brand_tier": 3.5,
            "rarity_score": 2.0,
            "age_years": 2.5,
            "demand_trend": 4.5,
            "shipping_included": True
        }
    },
    {
        "id": "nintendo_gameboy",
        "name": "Nintendo GameBoy Color Atomic Purple (1998)",
        "category_badge": "Retro Gaming",
        "data": {
            "title": "Nintendo GameBoy Color Handheld Console - Atomic Purple (CGB-001)",
            "brand": "Nintendo",
            "category": "electronics",
            "condition_score": 8.0,
            "condition_notes": "Tested and 100% fully functional. Sound is loud and clear, clean battery terminals, authentic battery cover.",
            "features": "Original OEM translucent purple shell, crisp screen, tested with Pokemon Red, buttons responsive",
            "original_retail_usd": 79.99,
            "purchase_cost": 25.0,
            "brand_tier": 4.0,
            "rarity_score": 4.0,
            "age_years": 26.0,
            "demand_trend": 4.9,
            "shipping_included": True
        }
    },
    {
        "id": "seiko_watch",
        "name": "Seiko 5 Automatic Diver 7S26 (SKX007)",
        "category_badge": "Watches & Luxury",
        "data": {
            "title": "Seiko SKX007 Automatic Diver 200m Watch",
            "brand": "Seiko",
            "category": "luxury",
            "condition_score": 8.5,
            "condition_notes": "Original dial and bezel with faint hair-line scratches on caseback. Keeping time within +/- 12 sec/day.",
            "features": "200m water resistance, automatic 7S26 movement, Jubilee stainless steel bracelet, Lumibrite hands",
            "original_retail_usd": 275.0,
            "purchase_cost": 90.0,
            "brand_tier": 3.5,
            "rarity_score": 4.5,
            "age_years": 12.0,
            "demand_trend": 4.7,
            "shipping_included": True
        }
    }
]

# ----------------- API Endpoints -----------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PriceCraft AI",
        "tabpfn_engine": "Prior Labs TabPFN-3.5 Active",
        "gemma_engine": "Google Gemma 2 Active",
        "serpapi_engine": "Live Competitor Radar Active",
        "elevenlabs_engine": "Neural Voiceover Active",
        "sentry_tracing": "Agent Telemetry Active",
    }

@app.get("/api/presets")
def get_presets():
    return SAMPLE_PRESETS

@app.post("/api/analyze")
def analyze_item(request: ItemAnalysisRequest):
    """
    Main orchestration agent:
    1. Traces workflow with Sentry Agent Tracing
    2. Runs Prior Labs TabPFN for tabular price and 14-day probability prediction
    3. Fetches live competitor comps via SerpApi
    4. Generates marketplace copy using Google Gemma 2
    5. Calculates net margins and return on investment
    """
    item_dict = request.model_dump()

    # Step 1: Prior Labs TabPFN Tabular Valuation
    with AgentSpan("tabular_valuation", "Prior Labs TabPFN-3.5") as span:
        valuation = predict_resale_metrics(item_dict)
        span.set_metadata("optimal_price", valuation["optimal_price"])
        span.set_metadata("confidence", valuation["confidence_score"])

    # Step 2: SerpApi Market Radar Comps
    search_query = f"{item_dict.get('brand')} {item_dict.get('title')}"
    with AgentSpan("market_comps", "SerpApi Google Shopping / eBay") as span:
        market_comps = fetch_competitor_comps(search_query, item_dict.get("category", "vintage"))
        span.set_metadata("competitor_count", market_comps.get("active_listings_count", 0))
        span.set_metadata("avg_competitor_price", market_comps.get("avg_competitor_price", 0))

    # Step 3: Google Gemma 2 Copywriting Agent
    with AgentSpan("listing_generation", "Google Gemma 2") as span:
        listing = generate_listing_with_gemma(item_dict, valuation)
        span.set_metadata("title_length", len(listing.get("ebay_title", "")))

    # Step 4: Unit Economics & Financial Margin Breakdown
    optimal_price = valuation["optimal_price"]
    purchase_cost = float(item_dict.get("purchase_cost", 0.0))
    # Standard blended resale platform fee (13.25% eBay standard + $0.30 fixed fee)
    platform_fee = round((optimal_price * 0.1325) + 0.30, 2)
    est_shipping = 0.0 if not item_dict.get("shipping_included") else 8.50
    net_profit = round(optimal_price - purchase_cost - platform_fee - est_shipping, 2)
    roi_percent = round((net_profit / max(purchase_cost, 1.0)) * 100, 1)

    unit_economics = {
        "listing_price": optimal_price,
        "purchase_cost": purchase_cost,
        "platform_fee": platform_fee,
        "est_shipping_cost": est_shipping,
        "net_profit_usd": net_profit,
        "roi_percent": roi_percent,
        "profit_margin_percent": round((net_profit / max(optimal_price, 1.0)) * 100, 1),
    }

    return {
        "status": "success",
        "valuation": valuation,
        "market_comps": market_comps,
        "listing": listing,
        "unit_economics": unit_economics,
    }

@app.post("/api/voiceover")
def create_voiceover(req: VoiceoverRequest):
    """Generates ElevenLabs TikTok/Reels narration."""
    with AgentSpan("voiceover_synthesis", "ElevenLabs Neural Audio") as span:
        result = generate_voiceover_promo(req.script)
        span.set_metadata("duration_sec", result.get("duration_sec", 0))
    return result

@app.get("/api/inventory")
def list_inventory():
    return get_all_items()

@app.post("/api/inventory")
def save_to_inventory(req: SaveInventoryRequest):
    item_id = save_item(req.item_data, req.valuation, req.listing)
    return {"status": "saved", "id": item_id}

@app.delete("/api/inventory/{item_id}")
def remove_from_inventory(item_id: int):
    delete_item(item_id)
    return {"status": "deleted", "id": item_id}

@app.get("/api/inventory/export")
def download_inventory_csv():
    """Exports inventory records to downloadable CSV for eBay File Exchange / Shopify import."""
    csv_content = export_inventory_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pricecraft_inventory_export.csv"}
    )

@app.get("/api/sentry/traces")
def get_traces():
    return {
        "traces": get_recent_traces(),
        "total_recorded": len(get_recent_traces())
    }

# ----------------- Serve Static Web Frontend -----------------

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
