"""Create three quick charts from the database and save them to docs/charts/.

Usage (from the project root):  python src/make_charts.py
"""
import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "olist.db"
CHART_DIR = ROOT / "docs" / "charts"

MONTHLY = """
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
       ROUND(SUM(oi.price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month
"""

CATEGORIES = """
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       ROUND(SUM(oi.price), 2) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY revenue DESC
LIMIT 10
"""

REVIEWS = """
WITH order_review AS (
    SELECT order_id, AVG(review_score) AS score FROM reviews GROUP BY order_id
)
SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 'Late' ELSE 'On time' END AS delivery,
       ROUND(AVG(r.score), 2) AS avg_review_score
FROM orders o
JOIN order_review r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery
"""


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(CHART_DIR / name, dpi=150)
    plt.close(fig)
    print(f"saved docs/charts/{name}")


def main() -> None:
    if not DB_PATH.exists():
        print("olist.db not found. Run  python src/load_data.py  first.")
        sys.exit(1)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        monthly = pd.read_sql_query(MONTHLY, conn)
        categories = pd.read_sql_query(CATEGORIES, conn)
        reviews = pd.read_sql_query(REVIEWS, conn)
    finally:
        conn.close()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(monthly["month"], monthly["revenue"], marker="o")
    ax.set_title("Monthly revenue (delivered orders)")
    ax.set_ylabel("Revenue (BRL)")
    ax.tick_params(axis="x", rotation=60)
    ax.set_xticks(ax.get_xticks()[::2])
    save(fig, "monthly_revenue.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    top = categories.iloc[::-1]
    ax.barh(top["category"], top["revenue"])
    ax.set_title("Top 10 product categories by revenue")
    ax.set_xlabel("Revenue (BRL)")
    save(fig, "top_categories.png")

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(reviews["delivery"], reviews["avg_review_score"])
    ax.set_ylim(0, 5)
    ax.set_title("Average review score by delivery status")
    ax.set_ylabel("Review score (1-5)")
    save(fig, "reviews_vs_delivery.png")


if __name__ == "__main__":
    main()
