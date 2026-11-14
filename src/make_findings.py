"""Build the 'Key findings' section of the README from the CSV files in outputs/.

Put this file in the src/ folder, then run it from the project root:

    python src/make_findings.py            # prints the text so you can check it
    python src/make_findings.py --write    # also updates README.md

Every number comes from the CSV files that run_sql.py saved in outputs/.
Running it again later is safe: it replaces the section instead of adding a second one.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
README = ROOT / "README.md"

MIN_STATE_ORDERS = 100  # ignore tiny states when ranking late-delivery rates
FIRST_COMPLETE_MONTH = "2017-01"  # earlier months have only a handful of orders
LAST_COMPLETE_MONTH = "2018-08"  # later months are incomplete

DASHBOARD_SECTION = """## Dashboard

![Overview](docs/01-overview.png)
![Monthly revenue trend](docs/02-monthly-revenue-trend.png)
![Top categories](docs/03-top-categories.png)
![Revenue and delivery by state](docs/04-revenue-and-delivery-by-state.png)
![Delivery vs reviews](docs/05-delivery-vs-reviews.png)

"""


def load(prefix: str) -> pd.DataFrame:
    matches = sorted(OUT_DIR.glob(f"{prefix}_*.csv"))
    if not matches:
        sys.exit(
            f"Could not find outputs/{prefix}_*.csv.\n"
            "Run  python src/run_sql.py sql/02_business_questions.sql  first."
        )
    return pd.read_csv(matches[0])


def build_findings() -> str:
    kpi = load("q1").iloc[0]
    monthly = load("q2")
    cats = load("q3")
    states = load("q4")
    delivery = load("q5")
    reviews = load("q6")
    repeat = load("q8").iloc[0]

    total_revenue = float(kpi["revenue"])
    lines = []

    # Revenue and orders
    lines.append(
        f"- **Revenue and orders:** {total_revenue / 1e6:.2f}M BRL from "
        f"{int(kpi['delivered_orders']):,} delivered orders placed by "
        f"{int(kpi['unique_customers']):,} unique customers "
        f"(average order value {kpi['avg_order_value']:.2f} BRL)."
    )

    # Growth over complete months only
    complete = monthly[
        (monthly["month"] >= FIRST_COMPLETE_MONTH) & (monthly["month"] <= LAST_COMPLETE_MONTH)
    ]
    if not complete.empty:
        first = complete.iloc[0]
        last = complete.iloc[-1]
        peak = complete.loc[complete["revenue"].idxmax()]
        lines.append(
            f"- **Growth:** monthly revenue rose from {first['revenue']:,.0f} BRL in {first['month']} "
            f"to a peak of {peak['revenue']:,.0f} BRL in {peak['month']}. "
            f"In {last['month']} it was {last['revenue']:,.0f} BRL."
        )

    # Categories
    c1, c2 = cats.iloc[0], cats.iloc[1]
    lines.append(
        f"- **Top categories:** {c1['category']} ({c1['revenue_share_pct']:.1f}% of revenue) and "
        f"{c2['category']} ({c2['revenue_share_pct']:.1f}%) lead. "
        f"The top 10 categories together make up {cats['revenue_share_pct'].sum():.1f}% of revenue."
    )

    # States
    s1 = states.iloc[0]
    top3 = states.head(3)
    top3_share = top3["revenue"].sum() / total_revenue * 100
    lines.append(
        f"- **Geography:** {s1['state']} alone generates {s1['revenue'] / total_revenue * 100:.1f}% of revenue. "
        f"The top three states ({', '.join(top3['state'])}) generate {top3_share:.1f}%."
    )

    # Delivery
    overall_late = delivery["late_orders"].sum() / delivery["delivered_orders"].sum() * 100
    eligible = delivery[delivery["delivered_orders"] >= MIN_STATE_ORDERS]
    if len(eligible) < 2:
        eligible = delivery
    eligible = eligible.sort_values("late_pct", ascending=False)
    worst, best = eligible.iloc[0], eligible.iloc[-1]
    lines.append(
        f"- **Delivery:** {overall_late:.1f}% of delivered orders arrived after the estimated date. "
        f"Among states with at least {MIN_STATE_ORDERS} delivered orders, the late rate ranged from "
        f"{best['late_pct']:.1f}% ({best['state']}) to {worst['late_pct']:.1f}% ({worst['state']})."
    )

    # Reviews
    late = reviews[reviews["delivery_status"] == "late"].iloc[0]
    on_time = reviews[reviews["delivery_status"] == "on time"].iloc[0]
    gap = on_time["avg_review_score"] - late["avg_review_score"]
    if gap > 0:
        caveat = (
            "Late delivery is associated with lower ratings, "
            "but this data alone does not show it is the only cause."
        )
    else:
        caveat = "In this data, late delivery is not associated with lower ratings."
    lines.append(
        f"- **Reviews:** late orders average {late['avg_review_score']:.2f} stars versus "
        f"{on_time['avg_review_score']:.2f} for on-time orders, a difference of {abs(gap):.2f} stars "
        f"({int(late['orders']):,} late and {int(on_time['orders']):,} on-time orders). {caveat}"
    )

    # Repeat customers
    lines.append(
        f"- **Customers:** {repeat['repeat_rate_pct']:.2f}% of customers "
        f"({int(repeat['repeat_customers']):,} of {int(repeat['customers']):,}) ordered more than once, "
        f"so {100 - repeat['repeat_rate_pct']:.1f}% bought only once."
    )

    return "## Key findings\n\n" + "\n".join(lines) + "\n\n"


def update_readme(findings: str) -> None:
    text = README.read_text(encoding="utf-8")
    start = text.find("## Key findings")
    if start == -1:
        sys.exit('README.md has no "## Key findings" heading to replace.')
    end = text.find("\n## ", start + 1)
    end = len(text) if end == -1 else end + 1  # keep the next heading

    before, after = text[:start], text[end:]
    section = findings
    if "## Dashboard" not in text:
        section = DASHBOARD_SECTION + findings
    README.write_text(before + section + after, encoding="utf-8")
    print("README.md updated.")


def main() -> None:
    findings = build_findings()
    print(findings)
    if "--write" in sys.argv:
        update_readme(findings)
    else:
        print("(Nothing was changed. Add --write to update README.md.)")


if __name__ == "__main__":
    main()