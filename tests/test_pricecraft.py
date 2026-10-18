"""
PriceCraft AI - Automated Test Suite
Tests TabPFN, Gemma 2, SerpApi, Sentry Telemetry, and Inventory Persistence.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app import app
from backend.tabpfn_engine import predict_resale_metrics
from backend.gemma_engine import generate_listing_with_gemma
from backend.serpapi_engine import fetch_competitor_comps
from backend.inventory_db import save_item, get_all_items, delete_item, export_inventory_csv

class TestPriceCraftAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_item = {
            "title": "Vintage 1994 Nike Spellout Windbreaker Jacket",
            "brand": "Nike",
            "category": "streetwear",
            "condition_score": 8.8,
            "condition_notes": "Very clean vintage condition, smooth zipper.",
            "features": "Colorblock purple/teal, embroidered swoosh, Large",
            "original_retail_usd": 85.0,
            "purchase_cost": 15.0,
            "brand_tier": 3.0,
            "rarity_score": 4.0,
            "age_years": 29.0,
            "demand_trend": 4.8,
            "shipping_included": True
        }

    def test_01_health_endpoint(self):
        """Verify API health check endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("tabpfn_engine", data)
        self.assertIn("gemma_engine", data)

    def test_02_presets_endpoint(self):
        """Verify instant demo presets are populated."""
        res = self.client.get("/api/presets")
        self.assertEqual(res.status_code, 200)
        presets = res.json()
        self.assertGreaterEqual(len(presets), 3)
        for p in presets:
            self.assertIn("name", p)
            self.assertIn("data", p)
            self.assertIn("title", p["data"])

    def test_03_tabpfn_pricing_engine(self):
        """Verify Prior Labs TabPFN resale prediction and elasticity curve."""
        valuation = predict_resale_metrics(self.sample_item)
        self.assertIn("optimal_price", valuation)
        self.assertIn("quick_sale_price", valuation)
        self.assertIn("patient_price", valuation)
        self.assertGreater(valuation["optimal_price"], 0)
        self.assertLessEqual(valuation["quick_sale_price"], valuation["optimal_price"])
        self.assertGreaterEqual(valuation["patient_price"], valuation["optimal_price"])
        self.assertIn("elasticity_curve", valuation)
        self.assertEqual(len(valuation["elasticity_curve"]), 5)
        self.assertGreater(valuation["confidence_score"], 70)

    def test_04_gemma_copywriting_engine(self):
        """Verify Google Gemma 2 generates strict 80-character title and copy."""
        valuation = predict_resale_metrics(self.sample_item)
        listing = generate_listing_with_gemma(self.sample_item, valuation)
        self.assertIn("ebay_title", listing)
        self.assertLessEqual(len(listing["ebay_title"]), 80, "eBay title must not exceed 80 chars!")
        self.assertIn("bullet_specs", listing)
        self.assertGreaterEqual(len(listing["bullet_specs"]), 3)
        self.assertIn("description_markdown", listing)
        self.assertIn("search_tags", listing)

    def test_05_serpapi_market_radar(self):
        """Verify SerpApi competitor comps extraction."""
        comps = fetch_competitor_comps("Nike Windbreaker Jacket", "streetwear")
        self.assertIn("min_competitor_price", comps)
        self.assertIn("avg_competitor_price", comps)
        self.assertIn("max_competitor_price", comps)
        self.assertGreater(comps["avg_competitor_price"], 0)
        self.assertGreaterEqual(len(comps.get("competitors", [])), 2)

    def test_06_full_analysis_pipeline(self):
        """Verify the complete multi-agent pipeline via HTTP POST."""
        res = self.client.post("/api/analyze", json=self.sample_item)
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(payload.get("status"), "success")
        self.assertIn("valuation", payload)
        self.assertIn("listing", payload)
        self.assertIn("market_comps", payload)
        self.assertIn("unit_economics", payload)
        self.assertGreater(payload["unit_economics"]["net_profit_usd"], 0)

    def test_07_inventory_crud_and_csv_export(self):
        """Verify inventory saving, CSV export, and deletion."""
        valuation = predict_resale_metrics(self.sample_item)
        listing = generate_listing_with_gemma(self.sample_item, valuation)

        # Save item
        item_id = save_item(self.sample_item, valuation, listing)
        self.assertIsInstance(item_id, int)

        # List items
        items = get_all_items()
        self.assertTrue(any(it["id"] == item_id for it in items))

        # Export CSV via endpoint
        res = self.client.get("/api/inventory/export")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "text/csv; charset=utf-8")
        csv_text = res.text
        self.assertIn("Item Title", csv_text)
        self.assertIn("TabPFN Optimal Price", csv_text)
        self.assertIn("Vintage 1994 Nike Spellout", csv_text)

        # Delete item
        delete_item(item_id)
        items_after = get_all_items()
        self.assertFalse(any(it["id"] == item_id for it in items_after))

    def test_08_sentry_telemetry_traces(self):
        """Verify Sentry Agent Tracing records step spans."""
        # Execute analysis to generate trace spans
        self.client.post("/api/analyze", json=self.sample_item)
        res = self.client.get("/api/sentry/traces")
        self.assertEqual(res.status_code, 200)
        traces = res.json().get("traces", [])
        self.assertGreater(len(traces), 0)
        span_tools = [t["tool"] for t in traces]
        self.assertTrue(any("TabPFN" in tool for tool in span_tools))

if __name__ == "__main__":
    unittest.main()
