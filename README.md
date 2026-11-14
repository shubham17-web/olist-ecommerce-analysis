# Olist Brazilian E-Commerce Analytics

An end-to-end data analytics project exploring Brazilian e-commerce business performance using the Olist dataset.

## Project Overview

This project investigates three key business questions:

- Where is revenue coming from?
- Which customers are most valuable?
- What is affecting delivery performance and customer satisfaction?

The project combines SQL, Python, exploratory data analysis, and an interactive Streamlit application to turn raw e-commerce data into actionable business insights.

## Tech Stack

- **Programming:** Python
- **Database:** PostgreSQL
- **Data Analysis:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn, Plotly
- **Application:** Streamlit
- **Version Control:** Git and GitHub

## Project Structure

```text
olist-ecommerce-analysis/
│
├── app.py
├── pages/
│   ├── 1_Executive_Overview.py
│   ├── 2_Revenue_Analysis.py
│   ├── 3_Customer_Analysis.py
│   └── 4_Delivery_Satisfaction.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
├── reports/
├── scripts/
├── sql/
├── .streamlit/
├── requirements.txt
└── README.md
```

## Project Workflow

1. **SQL Setup & Data Loading** — Loaded the Olist datasets into PostgreSQL.
2. **Data Cleaning** — Investigated missing values, duplicates, data types, and data-quality issues.
3. **Exploratory Data Analysis** — Analysed sales, customers, products, payments, reviews, and delivery performance.
4. **SQL Business Analysis** — Used joins, aggregations, CTEs, and window functions to answer business questions.
5. **Business Insights** — Investigated delivery delays, customer satisfaction, and seller performance.
6. **Streamlit Analytics Application** — Built an interactive application with four analytical pages.

## Key Business Findings

| Metric | Result |
|---|---:|
| Total orders | 99,441 |
| Unique customers | 96,096 |
| Item revenue | R$13,591,643.70 |
| Average review score | 4.09 / 5 |
| Late delivery rate | 8.11% |
| Repeat customers | 2,997 |

### Selected Insights

- Beauty and health was the highest-revenue product category.
- São Paulo generated the highest revenue among customer states.
- Repeat customers generated higher average revenue per customer than one-time customers.
- Late deliveries had a substantially higher low-review rate than on-time or early deliveries.
- Customer satisfaction varied across product categories and delivery regions.

These are descriptive findings from the analysed dataset, not proof of causation.

## Streamlit Application

The application contains four pages:

1. **Executive Overview** — Business KPIs.
2. **Revenue & Product Analysis** — Category revenue, top products, and monthly trends.
3. **Customer Analysis** — Repeat purchasing and RFM segmentation.
4. **Delivery & Customer Satisfaction** — Delivery performance, reviews, and category satisfaction.

## Installation & Setup

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd olist-ecommerce-analysis
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your local environment variables and PostgreSQL connection if you want to rerun the database-loading workflow.

Run the Streamlit application:

```bash
streamlit run app.py
```

## Important Notes

- The project uses the public Olist Brazilian E-Commerce dataset.
- Raw and processed datasets are kept separate.
- Database credentials and private environment variables must not be committed.
- RFM segments describe historical customer behaviour.
- Delivery and review relationships are observational, not causal.

## Future Improvements

- Power BI dashboard.
- Streamlit deployment.
- Additional customer retention analysis.
- More advanced predictive analytics.

## Author

BTech Information Technology Student

Interested in Data Analytics, Software Engineering, Python, SQL, and Machine Learning.