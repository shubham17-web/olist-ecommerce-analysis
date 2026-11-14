
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Customer Analysis | Olist",
    page_icon="👥",
    layout="wide"
)


# --------------------------------------------------
# 2. LOAD DATASETS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"


@st.cache_data
def load_data():

    customers = pd.read_csv(DATA_DIR / "customers_cleaned.csv")
    orders = pd.read_csv(DATA_DIR / "orders_cleaned.csv")
    order_items = pd.read_csv(DATA_DIR / "order_items_cleaned.csv")

    return customers, orders, order_items


# --------------------------------------------------
# 3. PAGE HEADER
# --------------------------------------------------

st.title("👥 Customer Analysis")

st.markdown("""
Understand customer purchasing behaviour, identify repeat
customers, and discover high-value customer segments.
""")

st.divider()


try:

    customers, orders, order_items = load_data()

    # --------------------------------------------------
    # 4. DATA PREPARATION
    # --------------------------------------------------

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"],
        errors="coerce"
    )

    order_items["price"] = pd.to_numeric(
        order_items["price"],
        errors="coerce"
    )

    # Map order records to actual unique customers
    customer_orders = orders.merge(
        customers[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="inner"
    )

    # One row per unique customer
    customer_summary = (
        customer_orders
        .groupby("customer_unique_id", as_index=False)
        .agg(
            frequency=("order_id", "nunique"),
            last_purchase=("order_purchase_timestamp", "max")
        )
    )

    # Calculate customer revenue
    revenue_data = (
        order_items
        .merge(
            orders[["order_id", "customer_id"]],
            on="order_id",
            how="inner"
        )
        .merge(
            customers[["customer_id", "customer_unique_id"]],
            on="customer_id",
            how="inner"
        )
    )

    customer_revenue = (
        revenue_data
        .groupby("customer_unique_id", as_index=False)
        .agg(
            monetary=("price", "sum")
        )
    )

    # Combine frequency, recency and monetary
    rfm = customer_summary.merge(
        customer_revenue,
        on="customer_unique_id",
        how="left"
    )

    rfm["monetary"] = rfm["monetary"].fillna(0)

    # Snapshot date: one day after the latest purchase
    snapshot_date = (
        customer_orders["order_purchase_timestamp"].max()
        + pd.Timedelta(days=1)
    )

    rfm["recency"] = (
        snapshot_date - rfm["last_purchase"]
    ).dt.days

    rfm = rfm.dropna(
        subset=["recency", "frequency", "monetary"]
    ).copy()

    # --------------------------------------------------
    # 5. CUSTOMER KPIs
    # --------------------------------------------------

    total_customers = customers["customer_unique_id"].nunique()

    repeat_customers = (
        rfm.loc[rfm["frequency"] > 1, "customer_unique_id"]
        .nunique()
    )

    one_time_customers = (
        rfm.loc[rfm["frequency"] == 1, "customer_unique_id"]
        .nunique()
    )

    repeat_rate = (
        repeat_customers / len(rfm) * 100
        if len(rfm) > 0 else 0
    )

    average_revenue = rfm["monetary"].mean()

    total_revenue = rfm["monetary"].sum()

    st.subheader("Customer Performance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Unique Customers",
        f"{total_customers:,}"
    )

    col2.metric(
        "Repeat Customers",
        f"{repeat_customers:,}"
    )

    col3.metric(
        "Repeat Customer Rate",
        f"{repeat_rate:.2f}%"
    )

    col4.metric(
        "Average Revenue / Customer",
        f"R$ {average_revenue:,.2f}"
    )

    st.divider()

    # --------------------------------------------------
    # 6. ONE-TIME VS REPEAT CUSTOMERS
    # --------------------------------------------------

    st.header("One-Time vs Repeat Customers")

    customer_type = pd.DataFrame({
        "Customer Type": ["One-Time", "Repeat"],
        "Customers": [
            one_time_customers,
            repeat_customers
        ]
    })

    col1, col2 = st.columns(2)

    with col1:

        fig_customer = px.pie(
            customer_type,
            names="Customer Type",
            values="Customers",
            hole=0.45,
            title="Customer Distribution"
        )

        st.plotly_chart(
            fig_customer,
            use_container_width=True
        )

    with col2:

        customer_type["Percentage"] = (
            customer_type["Customers"]
            / customer_type["Customers"].sum() * 100
        ).round(2)

        fig_customer_bar = px.bar(
            customer_type,
            x="Customer Type",
            y="Customers",
            text="Percentage",
            title="Customer Count by Type"
        )

        st.plotly_chart(
            fig_customer_bar,
            use_container_width=True
        )

    st.divider()

    # --------------------------------------------------
    # 7. RFM SCORING
    # --------------------------------------------------

    st.header("RFM Customer Segmentation")

    st.markdown("""
    Customers are scored from 1 to 5 for each RFM metric.

    - Recency: More recent purchases receive higher scores.
    - Frequency: More orders receive higher scores.
    - Monetary: Higher spending receives higher scores.
    """)

    if len(rfm) < 5:
        st.warning("Not enough customers to calculate RFM quintiles.")
        st.stop()

    # Rank first to handle duplicate values in quantile groups
    rfm["R_score"] = pd.qcut(
        rfm["recency"].rank(method="first"),
        5,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["M_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["RFM_score"] = (
        rfm["R_score"]
        + rfm["F_score"]
        + rfm["M_score"]
    )

    # --------------------------------------------------
    # 8. CUSTOMER SEGMENTS
    # --------------------------------------------------

    def assign_segment(row):

        r = row["R_score"]
        f = row["F_score"]

        if r >= 4 and f >= 4:
            return "Champions"

        elif f >= 4:
            return "Loyal Customers"

        elif r >= 4 and f >= 2:
            return "Potential Loyalists"

        elif r <= 2 and f >= 3:
            return "At Risk"

        elif r <= 2 and f <= 2:
            return "Hibernating"

        else:
            return "Others"

    rfm["segment"] = rfm.apply(
        assign_segment,
        axis=1
    )

    segment_summary = (
        rfm
        .groupby("segment", as_index=False)
        .agg(
            customers=("customer_unique_id", "nunique"),
            revenue=("monetary", "sum"),
            average_recency=("recency", "mean"),
            average_frequency=("frequency", "mean"),
            average_monetary=("monetary", "mean")
        )
        .sort_values(
            "customers",
            ascending=False
        )
    )

    segment_summary["revenue"] = (
        segment_summary["revenue"].round(2)
    )

    segment_summary["average_monetary"] = (
        segment_summary["average_monetary"].round(2)
    )

    st.subheader("Customer Segments")

    fig_segments = px.bar(
        segment_summary,
        x="segment",
        y="customers",
        color="segment",
        title="Number of Customers by RFM Segment",
        labels={
            "segment": "Customer Segment",
            "customers": "Number of Customers"
        }
    )

    st.plotly_chart(
        fig_segments,
        use_container_width=True
    )

    st.dataframe(
        segment_summary,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------
    # 9. TOP 10 CUSTOMERS
    # --------------------------------------------------

    st.header("Top 10 Customers by Revenue")

    top_customers = (
        rfm
        .sort_values(
            "monetary",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top_customers["monetary"] = (
        top_customers["monetary"].round(2)
    )

    top_customers = top_customers.rename(
        columns={
            "customer_unique_id": "Customer ID",
            "frequency": "Total Orders",
            "monetary": "Revenue (R$)",
            "recency": "Recency (Days)",
            "segment": "Customer Segment"
        }
    )

    st.dataframe(
        top_customers[
            [
                "Customer ID",
                "Total Orders",
                "Revenue (R$)",
                "Recency (Days)",
                "Customer Segment"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------
    # 10. CUSTOMER INSIGHTS
    # --------------------------------------------------

    st.header("Key Customer Insights")

    st.write(
        f"- One-time customers: **{one_time_customers:,}**"
    )

    st.write(
        f"- Repeat customers: **{repeat_customers:,}**"
    )

    st.write(
        f"- Repeat purchase rate: **{repeat_rate:.2f}%**"
    )

    st.write(
        f"- Total customer item revenue: "
        f"**R$ {total_revenue:,.2f}**"
    )

    st.caption(
        "RFM scores use quintiles within this dataset. "
        "They describe historical behaviour and are not "
        "predictions of future purchases."
    )


except FileNotFoundError as error:

    st.error("A required dataset could not be found.")
    st.code(str(error))

except KeyError as error:

    st.error("A required column is missing.")
    st.code(str(error))

except Exception as error:

    st.error("Something went wrong during customer analysis.")
    st.exception(error)
