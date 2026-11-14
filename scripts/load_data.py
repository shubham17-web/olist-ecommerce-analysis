
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.types import Text


# ----------------------------------
# 1. Load environment variables
# ----------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    raise ValueError("Missing database configuration in .env")


# ----------------------------------
# 2. Create database connection
# ----------------------------------

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ----------------------------------
# 3. Define CSV-to-table mapping
# ----------------------------------

DATA_DIR = PROJECT_ROOT / "data" / "raw"

FILES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation"
}


# ----------------------------------
# 4. Load CSV data into PostgreSQL
# ----------------------------------

def load_csv(file_name, table_name):

    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    print(f"\nLoading: {file_name}")

    first_chunk = True
    total_rows = 0

    for chunk in pd.read_csv(
        file_path,
        dtype="string",
        chunksize=50000
    ):

        # Initially store every column as TEXT.
        # We will create properly typed analytical
        # columns/views in later phases.

        column_types = {
            column: Text()
            for column in chunk.columns
        }

        chunk.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
            chunksize=1000,
            method="multi",
            dtype=column_types
        )

        total_rows += len(chunk)
        first_chunk = False

    print(f"Loaded {total_rows:,} rows into {table_name}")


# ----------------------------------
# 5. Load all nine datasets
# ----------------------------------

def main():

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("PostgreSQL connection successful!")

    for file_name, table_name in FILES.items():
        load_csv(file_name, table_name)

    print("\nAll datasets loaded successfully!")

    # ----------------------------------
    # 6. Verify row counts
    # ----------------------------------

    print("\nDATABASE VALIDATION")

    with engine.connect() as connection:

        for table_name in FILES.values():

            result = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            )

            count = result.scalar()

            print(f"{table_name}: {count:,} rows")


if __name__ == "__main__":
    main()
