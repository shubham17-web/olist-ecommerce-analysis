-- ============================================================
-- 05. KPI VALIDATION
-- Run these after the analysis scripts to compare results with
-- the project report/dashboard. Small differences may occur if
-- filters or join definitions differ.
-- ============================================================

-- 1. Dataset-level counts
SELECT
    (SELECT COUNT(*) FROM public.orders) AS orders,
    (SELECT COUNT(DISTINCT customer_unique_id) FROM public.customers) AS unique_customers,
    (SELECT COUNT(*) FROM public.order_items) AS order_items,
    (SELECT COUNT(*) FROM public.sellers) AS sellers,
    (SELECT COUNT(*) FROM public.products) AS products;

-- 2. Item revenue and freight, calculated directly from item rows
SELECT
    ROUND(SUM(NULLIF(price, '')::numeric), 2) AS item_revenue_brl,
    ROUND(SUM(NULLIF(freight_value, '')::numeric), 2) AS freight_brl
FROM public.order_items;

-- 3. Delivery denominator and late count
WITH delivered AS (
    SELECT
        order_id,
        NULLIF(order_delivered_customer_date, '')::timestamp AS delivered_ts,
        NULLIF(order_estimated_delivery_date, '')::timestamp AS estimated_ts
    FROM public.orders
    WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
      AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
)
SELECT
    COUNT(*) AS delivered_orders_with_estimated_date,
    COUNT(*) FILTER (WHERE delivered_ts > estimated_ts) AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE delivered_ts > estimated_ts)
        / NULLIF(COUNT(*), 0), 2) AS late_delivery_pct
FROM delivered;

-- 4. Average review score
SELECT
    ROUND(AVG(NULLIF(review_score, '')::numeric), 2) AS average_review_score,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(review_score, '')::integer IN (1, 2))
        / NULLIF(COUNT(NULLIF(review_score, '')), 0), 2) AS low_review_pct
FROM public.reviews;

-- 5. Top revenue category
SELECT
    p.product_category_name,
    ROUND(SUM(NULLIF(i.price, '')::numeric), 2) AS item_revenue_brl
FROM public.order_items i
JOIN public.products p ON p.product_id = i.product_id
GROUP BY p.product_category_name
ORDER BY item_revenue_brl DESC
LIMIT 5;
