"""Load the Olist CSV files into a SQLite database (olist.db).

Run from the project root:  python src/load_data.py
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "olist.db"

TABLES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Dates are stored as 'YYYY-MM-DD HH:MM:SS' text so SQLite date functions work on them.
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# The original files misspell these two column names.
RENAMES = {
    "products": {
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    }
}

INDEXES = [
    "CREATE INDEX idx_orders_customer ON orders(customer_id)",
    "CREATE INDEX idx_orders_status ON orders(order_status)",
    "CREATE INDEX idx_items_order ON order_items(order_id)",
    "CREATE INDEX idx_items_product ON order_items(product_id)",
    "CREATE INDEX idx_items_seller ON order_items(seller_id)",
    "CREATE INDEX idx_payments_order ON payments(order_id)",
    "CREATE INDEX idx_reviews_order ON reviews(order_id)",
    "CREATE INDEX idx_customers_id ON customers(customer_id)",
    "CREATE INDEX idx_products_id ON products(product_id)",
    "CREATE INDEX idx_sellers_id ON sellers(seller_id)",
]


def main() -> None:
    missing = [name for name in TABLES.values() if not (DATA_DIR / name).exists()]
    if missing:
        print("These files are missing from the data/ folder:")
        for name in missing:
            print(f"  - {name}")
        print("See data/README.txt for where to download them.")
        sys.exit(1)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        for table, filename in TABLES.items():
            df = pd.read_csv(DATA_DIR / filename)
            df = df.rename(columns=RENAMES.get(table, {}))
            for col in DATE_COLUMNS.get(table, []):
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
            df.to_sql(table, conn, index=False)
            print(f"{table:<22} {len(df):>8,} rows")
        for statement in INDEXES:
            conn.execute(statement)
        conn.commit()
    finally:
        conn.close()
    print(f"\nDone. Database written to {DB_PATH.name}")


if __name__ == "__main__":
    main()
