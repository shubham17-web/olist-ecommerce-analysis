-- ============================================================
-- 01. DATA QUALITY CHECKS
-- Olist Brazilian E-Commerce | PostgreSQL
-- Read-only queries. Assumes standard Olist table/column names.
-- ============================================================

-- 1. Row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM public.customers
UNION ALL SELECT 'orders', COUNT(*) FROM public.orders
UNION ALL SELECT 'order_items', COUNT(*) FROM public.order_items
UNION ALL SELECT 'payments', COUNT(*) FROM public.payments
UNION ALL SELECT 'reviews', COUNT(*) FROM public.reviews
UNION ALL SELECT 'products', COUNT(*) FROM public.products
UNION ALL SELECT 'sellers', COUNT(*) FROM public.sellers
ORDER BY table_name;

-- 2. Full-row duplicate checks
SELECT 'customers' AS table_name, COUNT(*) - COUNT(DISTINCT (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)) AS duplicate_rows FROM public.customers
UNION ALL
SELECT 'orders', COUNT(*) - COUNT(DISTINCT (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)) FROM public.orders
UNION ALL
SELECT 'order_items', COUNT(*) - COUNT(DISTINCT (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)) FROM public.order_items
UNION ALL
SELECT 'payments', COUNT(*) - COUNT(DISTINCT (order_id, payment_sequential, payment_type, payment_installments, payment_value)) FROM public.payments
UNION ALL
SELECT 'reviews', COUNT(*) - COUNT(DISTINCT (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp)) FROM public.reviews
UNION ALL
SELECT 'products', COUNT(*) - COUNT(DISTINCT (product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)) FROM public.products
UNION ALL
SELECT 'sellers', COUNT(*) - COUNT(DISTINCT (seller_id, seller_zip_code_prefix, seller_city, seller_state)) FROM public.sellers
ORDER BY table_name;

-- 3. Missing values in important order fields
SELECT
    COUNT(*) FILTER (WHERE NULLIF(order_purchase_timestamp, '') IS NULL) AS missing_purchase_timestamp,
    COUNT(*) FILTER (WHERE NULLIF(order_approved_at, '') IS NULL) AS missing_approved_at,
    COUNT(*) FILTER (WHERE NULLIF(order_delivered_carrier_date, '') IS NULL) AS missing_carrier_date,
    COUNT(*) FILTER (WHERE NULLIF(order_delivered_customer_date, '') IS NULL) AS missing_delivered_customer_date,
    COUNT(*) FILTER (WHERE NULLIF(order_estimated_delivery_date, '') IS NULL) AS missing_estimated_delivery_date
FROM public.orders;

-- 4. Missing review fields
SELECT
    COUNT(*) FILTER (WHERE NULLIF(review_comment_title, '') IS NULL) AS missing_review_titles,
    COUNT(*) FILTER (WHERE NULLIF(review_comment_message, '') IS NULL) AS missing_review_messages,
    COUNT(*) FILTER (WHERE NULLIF(review_score, '') IS NULL) AS missing_review_scores
FROM public.reviews;

-- 5. Missing product attributes
SELECT
    COUNT(*) FILTER (WHERE NULLIF(product_category_name, '') IS NULL) AS missing_category,
    COUNT(*) FILTER (WHERE NULLIF(product_weight_g, '') IS NULL) AS missing_weight,
    COUNT(*) FILTER (WHERE NULLIF(product_length_cm, '') IS NULL) AS missing_length,
    COUNT(*) FILTER (WHERE NULLIF(product_height_cm, '') IS NULL) AS missing_height,
    COUNT(*) FILTER (WHERE NULLIF(product_width_cm, '') IS NULL) AS missing_width
FROM public.products;

-- 6. Check natural/composite keys
-- Repeated order_id is expected in order_items and payments.
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT (order_id, order_item_id)) AS unique_order_item_keys,
    COUNT(*) - COUNT(DISTINCT (order_id, order_item_id)) AS duplicate_order_item_keys
FROM public.order_items;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT (order_id, payment_sequential)) AS unique_payment_keys,
    COUNT(*) - COUNT(DISTINCT (order_id, payment_sequential)) AS duplicate_payment_keys
FROM public.payments;

-- 7. Review IDs and order IDs can repeat; inspect separately
SELECT
    COUNT(*) AS review_rows,
    COUNT(DISTINCT review_id) AS unique_review_ids,
    COUNT(*) - COUNT(DISTINCT review_id) AS repeated_review_id_rows,
    COUNT(DISTINCT order_id) AS orders_with_reviews
FROM public.reviews;

-- 8. Referential integrity checks
SELECT COUNT(*) AS order_rows_without_customer
FROM public.orders o
LEFT JOIN public.customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;

SELECT COUNT(*) AS order_items_without_order
FROM public.order_items i
LEFT JOIN public.orders o ON o.order_id = i.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS order_items_without_product
FROM public.order_items i
LEFT JOIN public.products p ON p.product_id = i.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS order_items_without_seller
FROM public.order_items i
LEFT JOIN public.sellers s ON s.seller_id = i.seller_id
WHERE s.seller_id IS NULL;
