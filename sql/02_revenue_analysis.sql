-- ============================================================
-- 02. REVENUE & PRODUCT ANALYSIS
-- Revenue = item price; freight is kept separate.
-- ============================================================

-- 1. Overall business KPIs
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl,
    ROUND(SUM(NULLIF(i.freight_value, '')::numeric), 2) AS freight_revenue_brl,
    ROUND(AVG(NULLIF(i.price, '')::numeric), 2) AS average_item_price_brl
FROM public.orders o
JOIN public.customers c ON c.customer_id = o.customer_id
JOIN public.order_items i ON i.order_id = o.order_id;

-- 2. Revenue by product category
SELECT
    COALESCE(NULLIF(p.product_category_name, ''), 'unknown') AS category,
    COUNT(DISTINCT i.order_id) AS orders,
    COUNT(*) AS items_sold,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl
FROM public.order_items i
JOIN public.products p ON p.product_id = i.product_id
GROUP BY 1
ORDER BY item_revenue_brl DESC;

-- 3. Top 10 products by item revenue
SELECT
    i.product_id,
    COALESCE(NULLIF(p.product_category_name, ''), 'unknown') AS category,
    COUNT(*) AS items_sold,
    COUNT(DISTINCT i.order_id) AS orders,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl
FROM public.order_items i
LEFT JOIN public.products p ON p.product_id = i.product_id
GROUP BY i.product_id, p.product_category_name
ORDER BY item_revenue_brl DESC
LIMIT 10;

-- 4. Monthly revenue trend
SELECT
    DATE_TRUNC('month', NULLIF(o.order_purchase_timestamp, '')::timestamp)::date AS order_month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl,
    ROUND(SUM(NULLIF(i.freight_value, '')::numeric), 2) AS freight_brl
FROM public.orders o
JOIN public.order_items i ON i.order_id = o.order_id
WHERE NULLIF(o.order_purchase_timestamp, '') IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- 5. Revenue by customer state
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl
FROM public.orders o
JOIN public.customers c ON c.customer_id = o.customer_id
JOIN public.order_items i ON i.order_id = o.order_id
GROUP BY c.customer_state
ORDER BY item_revenue_brl DESC;

-- 6. Revenue by seller state
SELECT
    s.seller_state,
    COUNT(DISTINCT i.order_id) AS orders,
    COUNT(*) AS items_sold,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl
FROM public.order_items i
JOIN public.sellers s ON s.seller_id = i.seller_id
GROUP BY s.seller_state
ORDER BY item_revenue_brl DESC;

-- 7. Payment type distribution
SELECT
    payment_type,
    COUNT(*) AS payment_records,
    ROUND(SUM(NULLIF(payment_value, '')::numeric), 2) AS payment_value_brl,
    ROUND(100.0 * SUM(NULLIF(payment_value, '')::numeric)
        / NULLIF(SUM(SUM(NULLIF(payment_value, '')::numeric)) OVER (), 0), 2) AS pct_of_payment_value
FROM public.payments
GROUP BY payment_type
ORDER BY payment_value_brl DESC;

-- 8. Order status distribution
SELECT
    order_status,
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_orders
FROM public.orders
GROUP BY order_status
ORDER BY orders DESC;

-- 9. Average order value (AOV) using item revenue only
WITH order_revenue AS (
    SELECT order_id, SUM(NULLIF(price, '')::numeric) AS item_revenue
    FROM public.order_items
    GROUP BY order_id
)
SELECT
    COUNT(*) AS orders_with_items,
    ROUND(AVG(item_revenue), 2) AS average_order_item_revenue_brl,
    ROUND(SUM(item_revenue), 2) AS total_item_revenue_brl
FROM order_revenue;
