
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Delivery & Satisfaction | Olist",
    page_icon="🚚",
    layout="wide"
)


# --------------------------------------------------
# 2. LOAD DATASETS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"


@st.cache_data
def load_data():

    orders = pd.read_csv(DATA_DIR / "orders_cleaned.csv")
    customers = pd.read_csv(DATA_DIR / "customers_cleaned.csv")
    reviews = pd.read_csv(DATA_DIR / "reviews_cleaned.csv")
    order_items = pd.read_csv(DATA_DIR / "order_items_cleaned.csv")
    products = pd.read_csv(DATA_DIR / "products_cleaned.csv")

    return orders, customers, reviews, order_items, products


# --------------------------------------------------
# 3. PAGE HEADER
# --------------------------------------------------

st.title("🚚 Delivery & Customer Satisfaction")

st.markdown("""
Analyse delivery speed, late deliveries, customer reviews,
and product categories associated with lower satisfaction.
""")

st.divider()


try:

    orders, customers, reviews, order_items, products = load_data()

    # --------------------------------------------------
    # 4. DATA PREPARATION
    # --------------------------------------------------

    date_columns = [
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "order_purchase_timestamp"
    ]

    for column in date_columns:
        orders[column] = pd.to_datetime(
            orders[column],
            errors="coerce"
        )

    reviews["review_score"] = pd.to_numeric(
        reviews["review_score"],
        errors="coerce"
    )

    order_items["price"] = pd.to_numeric(
        order_items["price"],
        errors="coerce"
    )

    # Keep delivered orders with valid delivery dates
    delivery = orders[
        orders["order_status"] == "delivered"
    ].dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "order_purchase_timestamp"
        ]
    ).copy()

    # Calculate delivery duration
    delivery["delivery_days"] = (
        delivery["order_delivered_customer_date"]
        - delivery["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Calculate difference between actual and estimated dates
    delivery["delivery_difference"] = (
        delivery["order_delivered_customer_date"]
        - delivery["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    # Remove invalid negative delivery durations
    delivery = delivery[
        delivery["delivery_days"] >= 0
    ].copy()

    # Late delivery flag
    delivery["delivery_status"] = delivery[
        "delivery_difference"
    ].apply(
        lambda x: "Late" if x > 0 else "On Time / Early"
    )

    # Add customer state
    delivery = delivery.merge(
        customers[["customer_id", "customer_state"]],
        on="customer_id",
        how="left"
    )

    # Aggregate reviews to one row per order
    order_reviews = (
        reviews
        .dropna(subset=["review_score"])
        .groupby("order_id", as_index=False)
        .agg(
            average_review=("review_score", "mean"),
            review_records=("review_score", "count")
        )
    )

    # One row per delivered order with its review
    delivery_reviews = delivery.merge(
        order_reviews,
        on="order_id",
        how="inner"
    )

    delivery_reviews["review_category"] = (
        delivery_reviews["average_review"]
        .apply(
            lambda score: "Low (1–2)"
            if score <= 2
            else "Positive / Neutral (3–5)"
        )
    )

    # --------------------------------------------------
    # 5. FILTERS
    # --------------------------------------------------

    st.sidebar.header("Delivery Filters")

    available_states = sorted(
        delivery["customer_state"].dropna().unique()
    )

    selected_states = st.sidebar.multiselect(
        "Select customer states",
        options=available_states,
        default=available_states
    )

    filtered_delivery = delivery[
        delivery["customer_state"].isin(selected_states)
    ].copy()

    filtered_reviews = delivery_reviews[
        delivery_reviews["customer_state"].isin(selected_states)
    ].copy()

    if filtered_delivery.empty:
        st.warning("No delivery records found for the selected states.")
        st.stop()

    # --------------------------------------------------
    # 6. DELIVERY KPIs
    # --------------------------------------------------

    st.header("Delivery Performance")

    total_delivered = len(filtered_delivery)

    late_orders = filtered_delivery[
        filtered_delivery["delivery_status"] == "Late"
    ]

    late_count = len(late_orders)

    on_time_count = total_delivered - late_count

    late_rate = (
        late_count / total_delivered * 100
        if total_delivered > 0 else 0
    )

    average_delivery = filtered_delivery[
        "delivery_days"
    ].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Valid Delivered Orders",
        f"{total_delivered:,}"
    )

    col2.metric(
        "Average Delivery Time",
        f"{average_delivery:.2f} days"
    )

    col3.metric(
        "Late Orders",
        f"{late_count:,}"
    )

    col4.metric(
        "Late Delivery Rate",
        f"{late_rate:.2f}%"
    )

    st.divider()

    # --------------------------------------------------
    # 7. DELIVERY STATUS DISTRIBUTION
    # --------------------------------------------------

    st.subheader("On-Time vs Late Deliveries")

    delivery_distribution = pd.DataFrame({
        "Delivery Status": ["On Time / Early", "Late"],
        "Orders": [on_time_count, late_count]
    })

    col1, col2 = st.columns(2)

    with col1:

        fig_delivery = px.pie(
            delivery_distribution,
            names="Delivery Status",
            values="Orders",
            hole=0.45,
            title="Delivery Status Distribution"
        )

        st.plotly_chart(
            fig_delivery,
            use_container_width=True
        )

    with col2:

        fig_delivery_bar = px.bar(
            delivery_distribution,
            x="Delivery Status",
            y="Orders",
            text="Orders",
            title="Number of Orders by Delivery Status"
        )

        st.plotly_chart(
            fig_delivery_bar,
            use_container_width=True
        )

    st.divider()

    # --------------------------------------------------
    # 8. DELIVERY PERFORMANCE BY STATE
    # --------------------------------------------------

    st.header("Delivery Performance by Customer State")

    state_delivery = (
        filtered_delivery
        .groupby("customer_state", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            average_delivery_days=("delivery_days", "mean"),
            late_orders=(
                "delivery_status",
                lambda x: (x == "Late").sum()
            )
        )
    )

    state_delivery["late_percentage"] = (
        state_delivery["late_orders"]
        / state_delivery["total_orders"] * 100
    )

    state_delivery = state_delivery.sort_values(
        "late_percentage",
        ascending=False
    )

    fig_state = px.bar(
        state_delivery.head(15).sort_values(
            "late_percentage"
        ),
        x="late_percentage",
        y="customer_state",
        orientation="h",
        title="Top 15 States by Late Delivery Rate",
        labels={
            "late_percentage": "Late Delivery Rate (%)",
            "customer_state": "Customer State"
        },
        hover_data=[
            "total_orders",
            "late_orders",
            "average_delivery_days"
        ]
    )

    st.plotly_chart(
        fig_state,
        use_container_width=True
    )

    st.dataframe(
        state_delivery.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------
    # 9. DELIVERY TIME VS CUSTOMER REVIEW
    # --------------------------------------------------

    st.header("Delivery Time vs Customer Satisfaction")

    if not filtered_reviews.empty:

        review_comparison = (
            filtered_reviews
            .groupby("delivery_status", as_index=False)
            .agg(
                total_orders=("order_id", "nunique"),
                average_review=("average_review", "mean"),
                low_review_orders=(
                    "review_category",
                    lambda x: (x == "Low (1–2)").sum()
                )
            )
        )

        review_comparison["low_review_percentage"] = (
            review_comparison["low_review_orders"]
            / review_comparison["total_orders"] * 100
        )

        col1, col2 = st.columns(2)

        with col1:

            fig_review = px.bar(
                review_comparison,
                x="delivery_status",
                y="average_review",
                text="average_review",
                title="Average Review Score by Delivery Status",
                labels={
                    "delivery_status": "Delivery Status",
                    "average_review": "Average Review Score"
                }
            )

            st.plotly_chart(
                fig_review,
                use_container_width=True
            )

        with col2:

            fig_low_reviews = px.bar(
                review_comparison,
                x="delivery_status",
                y="low_review_percentage",
                text="low_review_percentage",
                title="Low Review Percentage by Delivery Status",
                labels={
                    "delivery_status": "Delivery Status",
                    "low_review_percentage": "Low Review Rate (%)"
                }
            )

            st.plotly_chart(
                fig_low_reviews,
                use_container_width=True
            )

        st.dataframe(
            review_comparison.round(2),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No matching review records for the selected states.")

    st.divider()

    # --------------------------------------------------
    # 10. PRODUCT CATEGORY SATISFACTION
    # --------------------------------------------------

    st.header("Customer Satisfaction by Product Category")

    # One review per order, joined to the order's product categories
    category_reviews = (
        order_items[["order_id", "product_id"]]
        .drop_duplicates()
        .merge(
            products[["product_id", "product_category_name"]],
            on="product_id",
            how="left"
        )
        .merge(
            order_reviews[["order_id", "average_review"]],
            on="order_id",
            how="inner"
        )
        .merge(
            delivery[["order_id", "customer_state"]],
            on="order_id",
            how="inner"
        )
    )

    category_reviews["product_category_name"] = (
        category_reviews["product_category_name"]
        .fillna("Unknown")
        .replace("", "Unknown")
    )

    category_reviews = category_reviews[
        category_reviews["customer_state"].isin(selected_states)
    ].copy()

    category_summary = (
        category_reviews
        .groupby("product_category_name", as_index=False)
        .agg(
            reviewed_orders=("order_id", "nunique"),
            average_review=("average_review", "mean"),
            low_review_orders=(
                "average_review",
                lambda x: (x <= 2).sum()
            )
        )
    )

    category_summary["low_review_percentage"] = (
        category_summary["low_review_orders"]
        / category_summary["reviewed_orders"] * 100
    )

    minimum_orders = st.slider(
        "Minimum reviewed orders per category",
        min_value=20,
        max_value=500,
        value=100,
        step=20
    )

    filtered_categories = category_summary[
        category_summary["reviewed_orders"] >= minimum_orders
    ].copy()

    filtered_categories = filtered_categories.sort_values(
        "low_review_percentage",
        ascending=False
    )

    if not filtered_categories.empty:

        fig_category = px.bar(
            filtered_categories.head(15).sort_values(
                "low_review_percentage"
            ),
            x="low_review_percentage",
            y="product_category_name",
            orientation="h",
            title="Categories with Highest Low Review Rates",
            labels={
                "low_review_percentage": "Low Review Rate (%)",
                "product_category_name": "Product Category"
            },
            hover_data=[
                "reviewed_orders",
                "low_review_orders",
                "average_review"
            ]
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

        st.dataframe(
            filtered_categories.round(2),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning(
            "No categories meet the selected minimum order count."
        )

    # --------------------------------------------------
    # 11. BUSINESS INTERPRETATION
    # --------------------------------------------------

    st.divider()

    st.header("Business Interpretation")

    st.markdown(f"""
    - **Average delivery time:** {average_delivery:.2f} days.
    - **Late delivery rate:** {late_rate:.2f}%.
    - **Late orders:** {late_count:,} out of {total_delivered:,} valid deliveries.

    Review scores and delivery performance are descriptive
    associations. They do not prove that delivery delays alone
    caused lower customer satisfaction.
    """)

    st.caption(
        "Delivery analysis excludes delivered orders with missing "
        "actual or estimated delivery dates. Review scores are "
        "aggregated to one average score per order before comparison."
    )


except FileNotFoundError as error:

    st.error("A required dataset could not be found.")
    st.code(str(error))


except KeyError as error:

    st.error("A required column is missing.")
    st.code(str(error))


except Exception as error:

    st.error("Something went wrong during delivery analysis.")
    st.exception(error)
