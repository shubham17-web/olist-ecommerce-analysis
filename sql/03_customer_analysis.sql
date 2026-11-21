-- ============================================================
-- 03. CUSTOMER ANALYSIS & RFM
-- Use customer_unique_id to identify the same customer across orders.
-- ============================================================

-- 1. Customer and repeat-purchase summary
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(COALESCE(NULLIF(i.price, '')::numeric, 0)) AS item_revenue
    FROM public.customers c
    JOIN public.orders o ON o.customer_id = c.customer_id
    LEFT JOIN public.order_items i ON i.order_id = o.order_id
    GROUP BY c.customer_unique_id
),
customer_level AS (
    SELECT customer_unique_id, order_count, item_revenue
    FROM customer_orders
)
SELECT
    COUNT(*) AS unique_customers,
    COUNT(*) FILTER (WHERE order_count = 1) AS one_time_customers,
    COUNT(*) FILTER (WHERE order_count > 1) AS repeat_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE order_count > 1) / NULLIF(COUNT(*), 0), 2) AS repeat_customer_pct,
    ROUND(AVG(item_revenue) FILTER (WHERE order_count = 1), 2) AS avg_revenue_one_time_brl,
    ROUND(AVG(item_revenue) FILTER (WHERE order_count > 1), 2) AS avg_revenue_repeat_brl
FROM customer_level;

-- 2. Top 20 customers by item revenue
WITH customer_revenue AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(COALESCE(NULLIF(i.price, '')::numeric, 0)) AS item_revenue
    FROM public.customers c
    JOIN public.orders o ON o.customer_id = c.customer_id
    LEFT JOIN public.order_items i ON i.order_id = o.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    customer_unique_id,
    order_count,
    ROUND(item_revenue, 2) AS item_revenue_brl
FROM customer_revenue
ORDER BY item_revenue DESC
LIMIT 20;

-- 3. RFM segmentation
-- Recency: days since most recent purchase in the dataset.
-- Frequency: number of distinct orders.
-- Monetary: total item revenue (freight excluded).
WITH customer_rfm AS (
    SELECT
        c.customer_unique_id,
        MAX(NULLIF(o.order_purchase_timestamp, '')::timestamp) AS last_purchase,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(COALESCE(NULLIF(i.price, '')::numeric, 0)) AS monetary
    FROM public.customers c
    JOIN public.orders o ON o.customer_id = c.customer_id
    LEFT JOIN public.order_items i ON i.order_id = o.order_id
    WHERE NULLIF(o.order_purchase_timestamp, '') IS NOT NULL
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT
        *,
        (SELECT MAX(last_purchase)::date FROM customer_rfm) - last_purchase::date AS recency_days,
        NTILE(5) OVER (ORDER BY (SELECT MAX(last_purchase) FROM customer_rfm) - last_purchase ASC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS monetary_score
    FROM customer_rfm
)
SELECT
    customer_unique_id,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary_brl,
    recency_score,
    frequency_score,
    monetary_score,
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
        WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'Recent Customers'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Hibernating'
        ELSE 'Potential Loyalists'
    END AS customer_segment
FROM rfm_scores
ORDER BY monetary DESC;

-- 4. RFM segment summary
WITH customer_rfm AS (
    SELECT
        c.customer_unique_id,
        MAX(NULLIF(o.order_purchase_timestamp, '')::timestamp) AS last_purchase,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(COALESCE(NULLIF(i.price, '')::numeric, 0)) AS monetary
    FROM public.customers c
    JOIN public.orders o ON o.customer_id = c.customer_id
    LEFT JOIN public.order_items i ON i.order_id = o.order_id
    WHERE NULLIF(o.order_purchase_timestamp, '') IS NOT NULL
    GROUP BY c.customer_unique_id
),
scored AS (
    SELECT
        *,
        (SELECT MAX(last_purchase)::date FROM customer_rfm) - last_purchase::date AS recency_days,
        NTILE(5) OVER (ORDER BY (SELECT MAX(last_purchase) FROM customer_rfm) - last_purchase ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM customer_rfm
),
segmented AS (
    SELECT *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'Recent Customers'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
            ELSE 'Potential Loyalists'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(AVG(frequency), 2) AS avg_orders,
    ROUND(AVG(monetary), 2) AS avg_item_revenue_brl
FROM segmented
GROUP BY segment
ORDER BY customers DESC;
