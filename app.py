
import streamlit as st

st.set_page_config(
    page_title="Olist Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛒 Olist E-Commerce Analytics")

st.markdown(
    "### Brazilian E-Commerce Business Intelligence"
)

st.write(
    "An interactive analytics platform exploring "
    "sales performance, customer behaviour, "
    "product performance, and delivery operations."
)

st.divider()

st.subheader("Explore Analytics")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Executive Overview")
    st.write("Explore overall business performance and KPIs.")

    st.markdown("### 💰 Revenue & Product Analysis")
    st.write("Discover revenue trends and category performance.")

with col2:
    st.markdown("### 👥 Customer Analysis")
    st.write("Explore customer behaviour and RFM segmentation.")

    st.markdown("### 🚚 Delivery & Satisfaction")
    st.write("Understand delivery performance and customer reviews.")

st.divider()

st.info(
    "Select an analytics page from the sidebar to get started."
)

st.caption(
    "Olist E-Commerce Analytics | Python • Pandas • Streamlit • Plotly"
)
