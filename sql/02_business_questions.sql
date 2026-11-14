-- Revenue = sum of item price (freight excluded) on delivered orders. Currency is Brazilian real (BRL).

-- Q1. Overall KPIs
SELECT COUNT(DISTINCT o.order_id) AS delivered_orders,
       COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
       ROUND(SUM(oi.price), 2) AS revenue,
       ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered';

-- Q2. Monthly revenue, month-over-month growth and running total
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(oi.price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY month
)
SELECT month,
       orders,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2) AS running_revenue
FROM monthly
ORDER BY month;

-- Q3. Top 10 product categories by revenue
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       COUNT(DISTINCT oi.order_id) AS orders,
       ROUND(SUM(oi.price), 2) AS revenue,
       ROUND(100.0 * SUM(oi.price) / SUM(SUM(oi.price)) OVER (), 1) AS revenue_share_pct
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;

-- Q4. Top 10 customer states by revenue
SELECT c.customer_state AS state,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.price), 2) AS revenue,
       ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY revenue DESC
LIMIT 10;

-- Q5. Delivery performance by state (late = delivered after the estimated date)
SELECT c.customer_state AS state,
       COUNT(*) AS delivered_orders,
       SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_orders,
       ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS late_pct,
       ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) AS avg_delivery_days
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY late_pct DESC;

-- Q6. Do late deliveries get lower review scores?
WITH order_review AS (
    SELECT order_id, AVG(review_score) AS score
    FROM reviews
    GROUP BY order_id
)
SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 'late' ELSE 'on time' END AS delivery_status,
       COUNT(*) AS orders,
       ROUND(AVG(r.score), 2) AS avg_review_score
FROM orders o
JOIN order_review r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;

-- Q7. Payment type mix
SELECT payment_type,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(payment_value), 2) AS total_value,
       ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 1) AS share_pct,
       ROUND(AVG(payment_installments), 1) AS avg_installments
FROM payments
GROUP BY payment_type
ORDER BY total_value DESC;

-- Q8. Repeat customer rate
WITH per_customer AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*) AS customers,
       SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;

-- Q9. Top 10 sellers by revenue with their average review score
WITH seller_revenue AS (
    SELECT oi.seller_id,
           COUNT(DISTINCT oi.order_id) AS orders,
           SUM(oi.price) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY oi.seller_id
),
seller_score AS (
    SELECT oi.seller_id, AVG(r.review_score) AS avg_score
    FROM order_items oi
    JOIN reviews r ON r.order_id = oi.order_id
    GROUP BY oi.seller_id
)
SELECT RANK() OVER (ORDER BY sr.revenue DESC) AS revenue_rank,
       sr.seller_id,
       s.seller_state,
       sr.orders,
       ROUND(sr.revenue, 2) AS revenue,
       ROUND(ss.avg_score, 2) AS avg_review_score
FROM seller_revenue sr
JOIN sellers s ON s.seller_id = sr.seller_id
LEFT JOIN seller_score ss ON ss.seller_id = sr.seller_id
ORDER BY revenue_rank
LIMIT 10;

-- Q10. Best-selling category in each state
WITH state_category AS (
    SELECT c.customer_state AS state,
           COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
           SUM(oi.price) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN products p ON p.product_id = oi.product_id
    LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY state, category
),
ranked AS (
    SELECT state, category, revenue,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY revenue DESC) AS rn
    FROM state_category
)
SELECT state, category, ROUND(revenue, 2) AS revenue
FROM ranked
WHERE rn = 1
ORDER BY revenue DESC;
