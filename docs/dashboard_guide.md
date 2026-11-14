# Dashboard guide (Power BI or Tableau)

Power BI and Tableau can read CSV files easily, but SQLite needs an extra driver. That is why
`python src/run_sql.py` saves every query result as a CSV in `outputs/`. Load those files.

## Pages

**1. Overview** (cards): revenue, delivered orders, average order value, repeat customer rate.
Source: `q1_overall_kpis.csv`, `q8_repeat_customer_rate.csv`.

**2. Trend:** line chart of monthly revenue with month-over-month growth.
Source: `q2_monthly_revenue_month_over_month_growth_and_running_total.csv`.
Tip: the first and last months of the dataset are incomplete. Filter them out or note it on the chart.

**3. Products:** bar chart of the top 10 categories and their revenue share.
Source: `q3_top_10_product_categories_by_revenue.csv`.

**4. Geography:** revenue by state, plus late delivery % by state.
Source: `q4_...` and `q5_...`.

**5. Delivery and reviews:** average review score for late vs on-time orders.
Source: `q6_...`.

## Rules for a dashboard recruiters like
- Put the most important number at the top left.
- Write a plain-English title for every chart that states the finding, for example
  "Late deliveries score 2 points lower in reviews" instead of "Review score by status".
- Use one or two colors and sort bars from largest to smallest.
- Export a screenshot of each page to `docs/` and embed them in the README.
