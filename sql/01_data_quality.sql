-- Run first. Before analysing anything, check what you are working with.

-- DQ1. Row count per table
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers;

-- DQ2. Orders by status
SELECT order_status,
       COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders
GROUP BY order_status
ORDER BY orders DESC;

-- DQ3. Date range of the data
SELECT MIN(order_purchase_timestamp) AS first_order,
       MAX(order_purchase_timestamp) AS last_order
FROM orders;

-- DQ4. Delivered orders that have no delivery date
SELECT COUNT(*) AS delivered_without_date
FROM orders
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL;

-- DQ5. Orders that have no items
SELECT COUNT(*) AS orders_without_items
FROM orders o
LEFT JOIN order_items oi ON oi.order_id = o.order_id
WHERE oi.order_id IS NULL;

-- DQ6. Duplicate review ids
SELECT COUNT(*) - COUNT(DISTINCT review_id) AS duplicate_review_rows
FROM reviews;

-- DQ7. Products with a missing category
SELECT COUNT(*) AS products_without_category
FROM products
WHERE product_category_name IS NULL;
