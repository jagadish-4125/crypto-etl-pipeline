"""
load.py
-------
LOAD stage of the ETL pipeline.

Connects to PostgreSQL and loads the transformed DataFrame using an
"upsert" strategy (INSERT ... ON CONFLICT DO UPDATE) so that re-running
the pipeline updates existing coins instead of creating duplicates.

Also appends a snapshot to a history table so you can track price
changes across pipeline runs over time.
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import Config
from src.logger import get_logger

logger = get_logger("LOAD")

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", "schema.sql")


def get_engine():
    """Creates a SQLAlchemy engine using settings from Config."""
    connection_string = Config.get_db_connection_string()
    engine = create_engine(connection_string)
    return engine


def ensure_schema_exists(engine):
    """Runs schema.sql to make sure target tables exist before loading."""
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    with engine.connect() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()

    logger.info("Schema verified/created successfully.")


def upsert_main_table(engine, df: pd.DataFrame):
    """
    Loads data into crypto_market_data using upsert logic:
    - If coin_id already exists -> UPDATE the row
    - If coin_id is new -> INSERT a new row
    """
    if df.empty:
        logger.warning("DataFrame is empty. Nothing to load.")
        return

    columns = df.columns.tolist()
    col_list = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])

    update_clause = ", ".join(
        [f"{col} = EXCLUDED.{col}" for col in columns if col != "coin_id"]
    )

    upsert_sql = text(f"""
        INSERT INTO crypto_market_data ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (coin_id)
        DO UPDATE SET {update_clause};
    """)

    records = df.to_dict(orient="records")

    with engine.connect() as conn:
        conn.execute(upsert_sql, records)
        conn.commit()

    logger.info(f"Upserted {len(records)} rows into crypto_market_data.")


def append_history_snapshot(engine, df: pd.DataFrame):
    """Appends a lightweight snapshot of this run into the history table."""
    if df.empty:
        return

    history_cols = [
        "coin_id", "symbol", "name", "current_price",
        "market_cap", "market_cap_rank", "total_volume",
        "price_change_pct_24h", "etl_loaded_at",
    ]
    history_df = df[[c for c in history_cols if c in df.columns]].copy()

    history_df.to_sql(
        "crypto_market_data_history",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    logger.info(f"Appended {len(history_df)} rows into crypto_market_data_history.")


def load(df: pd.DataFrame):
    """Main load entrypoint."""
    logger.info("Connecting to PostgreSQL...")
    engine = get_engine()

    try:
        # Quick connectivity test with a clear error message if it fails
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
    except Exception as e:
        logger.critical(f"Could not connect to PostgreSQL: {e}")
        raise

    ensure_schema_exists(engine)
    upsert_main_table(engine, df)
    append_history_snapshot(engine, df)
    logger.info("Load stage complete.")


if __name__ == "__main__":
    from src.extract import extract
    from src.transform import transform

    raw_df = extract()
    clean_df = transform(raw_df)
    load(clean_df)
