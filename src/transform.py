"""
transform.py
------------
TRANSFORM stage of the ETL pipeline.

Takes the raw DataFrame from the extract stage and:
  - Selects and renames relevant columns
  - Handles missing/null values
  - Fixes data types
  - Adds derived/calculated columns
  - Adds a load timestamp for auditability
"""

import pandas as pd
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.logger import get_logger

logger = get_logger("TRANSFORM")

# Mapping of raw API column names -> clean snake_case column names for our DB
COLUMN_MAP = {
    "id": "coin_id",
    "symbol": "symbol",
    "name": "name",
    "current_price": "current_price",
    "market_cap": "market_cap",
    "market_cap_rank": "market_cap_rank",
    "total_volume": "total_volume",
    "high_24h": "high_24h",
    "low_24h": "low_24h",
    "price_change_24h": "price_change_24h",
    "price_change_percentage_24h": "price_change_pct_24h",
    "price_change_percentage_7d_in_currency": "price_change_pct_7d",
    "circulating_supply": "circulating_supply",
    "total_supply": "total_supply",
    "ath": "all_time_high",
    "ath_change_percentage": "pct_from_ath",
    "last_updated": "api_last_updated",
}


def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting transformation...")

    if df.empty:
        logger.warning("Received empty DataFrame. Skipping transformation.")
        return df

    # 1. Keep only columns we care about (ignore the rest of the API payload)
    available_cols = [c for c in COLUMN_MAP.keys() if c in df.columns]
    df = df[available_cols].copy()

    # 2. Rename to clean column names
    df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in available_cols}, inplace=True)

    # 3. Handle missing values
    numeric_cols = [
        "current_price", "market_cap", "total_volume", "high_24h", "low_24h",
        "price_change_24h", "price_change_pct_24h", "price_change_pct_7d",
        "circulating_supply", "total_supply", "all_time_high", "pct_from_ath",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(0)

    df["market_cap_rank"] = pd.to_numeric(df.get("market_cap_rank"), errors="coerce").fillna(0).astype(int)

    # 4. Normalize text fields
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].str.upper().str.strip()
    if "name" in df.columns:
        df["name"] = df["name"].str.strip()

    # 5. Parse API timestamp into proper datetime
    if "api_last_updated" in df.columns:
        df["api_last_updated"] = pd.to_datetime(df["api_last_updated"], errors="coerce", utc=True)

    # 6. Derived columns -- this is the kind of thing that shows real ETL thinking
    df["volume_to_market_cap_ratio"] = (
        df["total_volume"] / df["market_cap"].replace(0, pd.NA)
    ).fillna(0).round(4)

    df["price_range_24h"] = (df["high_24h"] - df["low_24h"]).round(2)

    df["is_near_ath"] = df["pct_from_ath"] >= -10  # within 10% of all-time high

    # 7. Audit column: when this row was loaded by OUR pipeline
    df["etl_loaded_at"] = datetime.now(timezone.utc)

    # 8. Drop exact duplicate rows, if any
    before = len(df)
    df.drop_duplicates(subset=["coin_id"], inplace=True)
    after = len(df)
    if before != after:
        logger.info(f"Dropped {before - after} duplicate rows.")

    logger.info(f"Transformation complete. Final shape: {df.shape}")
    return df


if __name__ == "__main__":
    from src.extract import extract
    raw_df = extract()
    clean_df = transform(raw_df)
    print(clean_df.head())
    print(clean_df.dtypes)
