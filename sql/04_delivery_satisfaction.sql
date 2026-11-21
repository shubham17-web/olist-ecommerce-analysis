-- ============================================================
-- 04. DELIVERY PERFORMANCE & CUSTOMER SATISFACTION
-- Reviews are order-level. Aggregate review data before joining
-- to order_items to avoid multiplying review rows.
-- ============================================================

-- 1. Delivery time and lateness
WITH delivery AS (
    SELECT
        order_id,
        NULLIF(order_purchase_timestamp, '')::timestamp AS purchase_ts,
        NULLIF(order_delivered_customer_date, '')::timestamp AS delivered_ts,
        NULLIF(order_estimated_delivery_date, '')::timestamp AS estimated_ts
    FROM public.orders
    WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
      AND NULLIF(order_purchase_timestamp, '') IS NOT NULL
      AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
)
SELECT
    COUNT(*) AS delivered_orders,
    ROUND(AVG(EXTRACT(EPOCH FROM (delivered_ts - purchase_ts)) / 86400.0)::numeric, 2) AS avg_delivery_days,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY EXTRACT(EPOCH FROM (delivered_ts - purchase_ts)) / 86400.0))::numeric, 2) AS median_delivery_days,
    COUNT(*) FILTER (WHERE delivered_ts > estimated_ts) AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE delivered_ts > estimated_ts) / NULLIF(COUNT(*), 0), 2) AS late_delivery_pct
FROM delivery;

-- 2. Average review score: late vs on-time/early
WITH delivery AS (
    SELECT
        order_id,
        NULLIF(order_delivered_customer_date, '')::timestamp AS delivered_ts,
        NULLIF(order_estimated_delivery_date, '')::timestamp AS estimated_ts
    FROM public.orders
    WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
      AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
),
review_by_order AS (
    SELECT
        order_id,
        AVG(NULLIF(review_score, '')::numeric) AS review_score
    FROM public.reviews
    WHERE NULLIF(review_score, '') IS NOT NULL
    GROUP BY order_id
)
SELECT
    CASE WHEN d.delivered_ts > d.estimated_ts THEN 'Late' ELSE 'On-time/Early' END AS delivery_group,
    COUNT(*) AS orders,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r.review_score <= 2) / NULLIF(COUNT(r.review_score), 0), 2) AS low_review_pct
FROM delivery d
JOIN review_by_order r ON r.order_id = d.order_id
GROUP BY 1
ORDER BY 1;

-- 3. Monthly late-delivery rate
SELECT
    DATE_TRUNC('month', NULLIF(order_purchase_timestamp, '')::timestamp)::date AS order_month,
    COUNT(*) FILTER (
        WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
          AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
    ) AS delivered_orders_with_estimate,
    COUNT(*) FILTER (
        WHERE NULLIF(order_delivered_customer_date, '')::timestamp >
              NULLIF(order_estimated_delivery_date, '')::timestamp
    ) AS late_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
              AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
              AND NULLIF(order_delivered_customer_date, '')::timestamp >
                  NULLIF(order_estimated_delivery_date, '')::timestamp
        )
        / NULLIF(COUNT(*) FILTER (
            WHERE NULLIF(order_delivered_customer_date, '') IS NOT NULL
              AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL
        ), 0), 2
    ) AS late_delivery_pct
FROM public.orders
WHERE NULLIF(order_purchase_timestamp, '') IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- 4. Review score distribution
SELECT
    NULLIF(review_score, '')::integer AS review_score,
    COUNT(*) AS review_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_reviews
FROM public.reviews
WHERE NULLIF(review_score, '') IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- 5. Average review by customer state
WITH review_by_order AS (
    SELECT order_id, AVG(NULLIF(review_score, '')::numeric) AS review_score
    FROM public.reviews
    WHERE NULLIF(review_score, '') IS NOT NULL
    GROUP BY order_id
)
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS orders_with_reviews,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r.review_score <= 2)
        / NULLIF(COUNT(r.review_score), 0), 2) AS low_review_pct
FROM public.orders o
JOIN public.customers c ON c.customer_id = o.customer_id
JOIN review_by_order r ON r.order_id = o.order_id
GROUP BY c.customer_state
ORDER BY avg_review_score ASC;

-- 6. Review score by product category
-- First calculate one review score per order, then join to item/category data.
WITH review_by_order AS (
    SELECT order_id, AVG(NULLIF(review_score, '')::numeric) AS review_score
    FROM public.reviews
    WHERE NULLIF(review_score, '') IS NOT NULL
    GROUP BY order_id
),
category_order AS (
    SELECT DISTINCT
        i.order_id,
        COALESCE(NULLIF(p.product_category_name, ''), 'unknown') AS category
    FROM public.order_items i
    JOIN public.products p ON p.product_id = i.product_id
)
SELECT
    co.category,
    COUNT(*) AS reviewed_category_orders,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM category_order co
JOIN review_by_order r ON r.order_id = co.order_id
GROUP BY co.category
ORDER BY avg_review_score ASC;
