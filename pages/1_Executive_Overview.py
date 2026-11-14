
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Executive Overview | Olist",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# 2. LOAD DATASETS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"


@st.cache_data
def load_data():

    datasets = {
        "customers": "customers_cleaned.csv",
        "orders": "orders_cleaned.csv",
        "order_items": "order_items_cleaned.csv",
        "reviews": "reviews_cleaned.csv"
    }

    data = {}

    for name, filename in datasets.items():

        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {file_path}"
            )

        data[name] = pd.read_csv(file_path)

    return data


# --------------------------------------------------
# 3. PAGE HEADER
# --------------------------------------------------

st.title("📊 Executive Overview")

st.markdown("""
A high-level overview of Olist's Brazilian e-commerce
business performance.
""")

st.divider()


# --------------------------------------------------
# 4. CALCULATE BUSINESS KPIs
# --------------------------------------------------

try:

    data = load_data()

    customers = data["customers"]
    orders = data["orders"]
    order_items = data["order_items"]
    reviews = data["reviews"]

    # Total orders
    total_orders = orders["order_id"].nunique()

    # Unique customers
    total_customers = customers["customer_unique_id"].nunique()

    # Total item revenue
    order_items["price"] = pd.to_numeric(
        order_items["price"],
        errors="coerce"
    )

    total_revenue = order_items["price"].sum()

    # Average review score
    reviews["review_score"] = pd.to_numeric(
        reviews["review_score"],
        errors="coerce"
    )

    average_review = reviews["review_score"].mean()

    # Late delivery percentage
    delivered_orders = orders[
        orders["order_status"] == "delivered"
    ].copy()

    delivered_orders["actual_delivery"] = pd.to_datetime(
        delivered_orders["order_delivered_customer_date"],
        errors="coerce"
    )

    delivered_orders["estimated_delivery"] = pd.to_datetime(
        delivered_orders["order_estimated_delivery_date"],
        errors="coerce"
    )

    valid_deliveries = delivered_orders.dropna(
        subset=[
            "actual_delivery",
            "estimated_delivery"
        ]
    ).copy()

    late_orders = valid_deliveries[
        valid_deliveries["actual_delivery"]
        > valid_deliveries["estimated_delivery"]
    ]

    late_delivery_percentage = (
        len(late_orders) / len(valid_deliveries) * 100
        if len(valid_deliveries) > 0
        else 0
    )

    
# --------------------------------------------------
# 5. DISPLAY KPI CARDS
# --------------------------------------------------

    st.subheader("Business Performance KPIs")

    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")

    with col1:
        with st.container(border=True):
            st.metric(
                label="Total Orders",
                value=f"{total_orders:,}"
            )

    with col2:
        with st.container(border=True):
            st.metric(
                label="Unique Customers",
                value=f"{total_customers:,}"
            )

    with col3:
        with st.container(border=True):
            st.metric(
                label="Total Item Revenue",
                value=f"R$ {total_revenue:,.2f}"
            )

    with col4:
        with st.container(border=True):
            st.metric(
                label="Average Review Score",
                value=f"{average_review:.2f} / 5"
                if pd.notna(average_review)
                else "N/A"
            )

    with col5:
        with st.container(border=True):
            st.metric(
                label="Late Delivery Rate",
                value=f"{late_delivery_percentage:.2f}%"
            )

    st.divider()

    # --------------------------------------------------
    # 6. KPI DEFINITIONS
    # --------------------------------------------------

    st.subheader("Understanding the KPIs")

    kpi_info = {
        "Total Orders": (
            "Count of distinct order IDs across all order statuses."
        ),
        "Unique Customers": (
            "Count of distinct customer_unique_id values."
        ),
        "Total Item Revenue": (
            "Sum of product prices from order_items. "
            "Freight is excluded."
        ),
        "Average Review Score": (
            "Mean of available review scores on a scale of 1 to 5."
        ),
        "Late Delivery Rate": (
            "Delivered orders arriving after their estimated date, "
            "divided by delivered orders with valid actual and "
            "estimated delivery dates."
        )
    }

    for title, description in kpi_info.items():
        st.markdown(f"**{title}:** {description}")

    st.divider()

    # --------------------------------------------------
    # 7. DATA COVERAGE
    # --------------------------------------------------

    st.subheader("Delivery Data Coverage")

    coverage_col1, coverage_col2, coverage_col3 = st.columns(3)

    with coverage_col1:
        st.metric(
            "Delivered Orders",
            f"{len(delivered_orders):,}"
        )

    with coverage_col2:
        st.metric(
            "Valid Delivery Records",
            f"{len(valid_deliveries):,}"
        )

    with coverage_col3:
        st.metric(
            "Late Orders",
            f"{len(late_orders):,}"
        )

    st.caption(
        "Delivery rate calculations exclude delivered orders "
        "with missing actual or estimated delivery dates."
    )

except FileNotFoundError as error:

    st.error("A required dataset could not be found.")
    st.code(str(error))

except KeyError as error:

    st.error(
        "A required column is missing from one of your datasets."
    )
    st.code(str(error))

except Exception as error:

    st.error("Unable to calculate the business KPIs.")
    st.exception(error)
