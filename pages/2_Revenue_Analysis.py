
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Revenue Analysis | Olist",
    page_icon="💰",
    layout="wide"
)


# --------------------------------------------------
# 2. LOAD DATASETS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"


@st.cache_data
def load_data():

    order_items = pd.read_csv(
        DATA_DIR / "order_items_cleaned.csv"
    )

    orders = pd.read_csv(
        DATA_DIR / "orders_cleaned.csv"
    )

    products = pd.read_csv(
        DATA_DIR / "products_cleaned.csv"
    )

    return order_items, orders, products


# --------------------------------------------------
# 3. PAGE HEADER
# --------------------------------------------------

st.title("💰 Revenue & Product Analysis")

st.markdown("""
Explore product revenue, category performance,
top-selling products, and monthly sales trends.
""")

st.divider()


# --------------------------------------------------
# 4. DATA PREPARATION
# --------------------------------------------------

try:

    order_items, orders, products = load_data()

    # Convert price to numeric
    order_items["price"] = pd.to_numeric(
        order_items["price"],
        errors="coerce"
    )

    # Remove rows without valid price or product ID
    order_items = order_items.dropna(
        subset=["price", "product_id"]
    ).copy()

    # Merge order items with product categories
    revenue_data = order_items.merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left"
    )

    revenue_data["product_category_name"] = (
        revenue_data["product_category_name"]
        .fillna("Unknown")
        .replace("", "Unknown")
    )

    # Merge with order purchase dates
    monthly_data = order_items.merge(
        orders[["order_id", "order_purchase_timestamp"]],
        on="order_id",
        how="left"
    )

    monthly_data["order_purchase_timestamp"] = pd.to_datetime(
        monthly_data["order_purchase_timestamp"],
        errors="coerce"
    )

    monthly_data = monthly_data.dropna(
        subset=["order_purchase_timestamp"]
    ).copy()

    monthly_data["month"] = (
        monthly_data["order_purchase_timestamp"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # --------------------------------------------------
    # 5. REVENUE KPIs
    # --------------------------------------------------

    total_revenue = revenue_data["price"].sum()

    total_items = len(revenue_data)

    total_products = revenue_data["product_id"].nunique()

    average_item_price = revenue_data["price"].mean()

    st.subheader("Revenue Performance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Item Revenue",
        f"R$ {total_revenue:,.2f}"
    )

    col2.metric(
        "Items Sold",
        f"{total_items:,}"
    )

    col3.metric(
        "Unique Products Sold",
        f"{total_products:,}"
    )

    col4.metric(
        "Average Item Price",
        f"R$ {average_item_price:,.2f}"
    )

    st.divider()

    # --------------------------------------------------
    # 6. CATEGORY REVENUE ANALYSIS
    # --------------------------------------------------

    st.header("Revenue by Product Category")

    category_revenue = (
        revenue_data
        .groupby("product_category_name", as_index=False)
        .agg(
            total_revenue=("price", "sum"),
            total_items=("product_id", "count")
        )
        .sort_values(
            "total_revenue",
            ascending=False
        )
    )

    top_n = st.slider(
        "Select number of categories",
        min_value=5,
        max_value=20,
        value=10
    )

    top_categories = category_revenue.head(top_n)

    fig_category = px.bar(
        top_categories.sort_values("total_revenue"),
        x="total_revenue",
        y="product_category_name",
        orientation="h",
        title=f"Top {top_n} Categories by Revenue",
        labels={
            "total_revenue": "Revenue (R$)",
            "product_category_name": "Product Category"
        },
        hover_data={
            "total_items": True
        }
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

    st.divider()

    # --------------------------------------------------
    # 7. TOP 10 PRODUCTS
    # --------------------------------------------------

    st.header("Top 10 Products by Revenue")

    product_revenue = (
        revenue_data
        .groupby("product_id", as_index=False)
        .agg(
            total_revenue=("price", "sum"),
            total_items=("product_id", "count")
        )
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .head(10)
    )

    product_revenue["total_revenue"] = (
        product_revenue["total_revenue"].round(2)
    )

    st.dataframe(
        product_revenue,
        use_container_width=True,
        hide_index=True
    )

    fig_products = px.bar(
        product_revenue.sort_values("total_revenue"),
        x="total_revenue",
        y="product_id",
        orientation="h",
        title="Top 10 Products by Revenue",
        labels={
            "total_revenue": "Revenue (R$)",
            "product_id": "Product ID"
        }
    )

    st.plotly_chart(
        fig_products,
        use_container_width=True
    )

    st.divider()

    # --------------------------------------------------
    # 8. MONTHLY REVENUE TREND
    # --------------------------------------------------

    st.header("Monthly Revenue Trend")

    monthly_revenue = (
        monthly_data
        .groupby("month", as_index=False)
        .agg(
            total_revenue=("price", "sum")
        )
        .sort_values("month")
    )

    fig_monthly = px.line(
        monthly_revenue,
        x="month",
        y="total_revenue",
        markers=True,
        title="Monthly Item Revenue",
        labels={
            "month": "Month",
            "total_revenue": "Revenue (R$)"
        }
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )

    st.caption(
        "Monthly revenue is based on order purchase dates. "
        "Incomplete months should be interpreted carefully."
    )

    st.divider()

    # --------------------------------------------------
    # 9. CATEGORY SUMMARY TABLE
    # --------------------------------------------------

    st.header("Category Performance Table")

    category_revenue["average_item_price"] = (
        category_revenue["total_revenue"]
        / category_revenue["total_items"]
    ).round(2)

    category_revenue["total_revenue"] = (
        category_revenue["total_revenue"].round(2)
    )

    category_revenue = category_revenue.rename(
        columns={
            "product_category_name": "Category",
            "total_revenue": "Revenue (R$)",
            "total_items": "Items Sold",
            "average_item_price": "Average Item Price (R$)"
        }
    )

    st.dataframe(
        category_revenue,
        use_container_width=True,
        hide_index=True
    )

except FileNotFoundError as error:

    st.error("A required dataset could not be found.")
    st.code(str(error))

except KeyError as error:

    st.error("A required column is missing.")
    st.code(str(error))

except Exception as error:

    st.error("Something went wrong.")
    st.exception(error)
