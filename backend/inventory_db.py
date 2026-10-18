"""
PriceCraft AI - Reseller Inventory & Valuation Database
Lightweight SQLite store for tracking catalog items, valuations, and listing status.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "inventory.db")

def init_db():
    """Initializes the database schema."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                purchase_cost REAL DEFAULT 0.0,
                optimal_price REAL,
                quick_sale_price REAL,
                patient_price REAL,
                condition_score REAL,
                status TEXT DEFAULT 'draft',
                ebay_title TEXT,
                description_markdown TEXT,
                bullet_specs TEXT,
                search_tags TEXT,
                social_hook TEXT,
                factors_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_item(item_data: Dict[str, Any], valuation: Dict[str, Any], listing: Dict[str, Any]) -> int:
    """Saves a new item with valuation and copy into the inventory table."""
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory_items (
                title, brand, category, purchase_cost, optimal_price, quick_sale_price,
                patient_price, condition_score, status, ebay_title, description_markdown,
                bullet_specs, search_tags, social_hook, factors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_data.get("title", "Untitled Item"),
            item_data.get("brand", "Unknown"),
            item_data.get("category", "streetwear"),
            float(item_data.get("purchase_cost", 0.0)),
            float(valuation.get("optimal_price", 0.0)),
            float(valuation.get("quick_sale_price", 0.0)),
            float(valuation.get("patient_price", 0.0)),
            float(item_data.get("condition_score", 8.0)),
            "active_listed",
            listing.get("ebay_title", ""),
            listing.get("description_markdown", ""),
            json.dumps(listing.get("bullet_specs", [])),
            json.dumps(listing.get("search_tags", [])),
            listing.get("social_hook", ""),
            json.dumps(valuation.get("factors", [])),
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_items() -> List[Dict[str, Any]]:
    """Retrieves all inventory items."""
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory_items ORDER BY created_at DESC")
        rows = cursor.fetchall()
        items = []
        for r in rows:
            d = dict(r)
            d["bullet_specs"] = json.loads(d["bullet_specs"]) if d["bullet_specs"] else []
            d["search_tags"] = json.loads(d["search_tags"]) if d["search_tags"] else []
            d["factors"] = json.loads(d["factors_json"]) if d["factors_json"] else []
            items.append(d)
        return items

def delete_item(item_id: int):
    """Deletes an item by ID."""
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))
        conn.commit()

def export_inventory_csv() -> str:
    """Exports inventory records to a standard CSV string for eBay/Shopify import."""
    import io
    import csv

    items = get_all_items()
    output = io.StringIO()
    writer = csv.writer(output)

    # Header columns
    writer.writerow([
        "ID", "Item Title", "Brand", "Category", "Condition Score",
        "Purchase Cost (USD)", "TabPFN Optimal Price (USD)", "Floor Price (USD)",
        "Ceiling Price (USD)", "Projected Net Profit (USD)", "Status",
        "eBay SEO Title", "Search Tags", "Created Date"
    ])

    for it in items:
        price = it.get("optimal_price", 0.0)
        cost = it.get("purchase_cost", 0.0)
        fee = round((price * 0.1325) + 0.30, 2)
        net_profit = round(price - cost - fee - 8.50, 2)
        tags_str = ", ".join(it.get("search_tags", []))

        writer.writerow([
            it.get("id"),
            it.get("title"),
            it.get("brand"),
            it.get("category"),
            it.get("condition_score"),
            f"{cost:.2f}",
            f"{price:.2f}",
            f"{it.get('quick_sale_price', 0.0):.2f}",
            f"{it.get('patient_price', 0.0):.2f}",
            f"{net_profit:.2f}",
            it.get("status"),
            it.get("ebay_title"),
            tags_str,
            it.get("created_at")
        ])

    return output.getvalue()

