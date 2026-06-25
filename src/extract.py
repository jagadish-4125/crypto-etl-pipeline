"""
extract.py
----------
EXTRACT stage of the ETL pipeline.

Pulls live cryptocurrency market data from the CoinGecko public API
(no API key required). Handles pagination, retries, and rate-limit
backoff -- the realistic concerns of working with any third-party API.
"""

import time
import requests
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import Config
from src.logger import get_logger

logger = get_logger("EXTRACT")


def fetch_market_data(max_retries: int = 3, backoff_seconds: int = 5) -> list[dict]:
    """
    Fetches top N coins by market cap from CoinGecko's /coins/markets endpoint.

    Returns:
        A list of dicts, each representing one coin's raw market data.
    """
    url = f"{Config.API_BASE_URL}/coins/markets"
    params = {
        "vs_currency": Config.API_CURRENCY,
        "order": "market_cap_desc",
        "per_page": Config.API_TOP_N_COINS,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Requesting data from API (attempt {attempt}/{max_retries})...")
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                # Rate limited -- wait and retry
                logger.warning(f"Rate limited by API. Backing off for {backoff_seconds}s...")
                time.sleep(backoff_seconds)
                continue

            response.raise_for_status()  # raises HTTPError for 4xx/5xx
            data = response.json()

            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("API returned empty or unexpected data format.")

            logger.info(f"Successfully extracted {len(data)} records from API.")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on attempt {attempt}: {e}")
            if attempt == max_retries:
                logger.critical("Max retries reached. Aborting extraction.")
                raise
            time.sleep(backoff_seconds)

    return []


def extract() -> pd.DataFrame:
    """
    Main extract entrypoint. Returns raw data as a pandas DataFrame.
    """
    raw_data = fetch_market_data()
    df = pd.DataFrame(raw_data)
    logger.info(f"Raw DataFrame shape: {df.shape}")
    return df


if __name__ == "__main__":
    # Allows running this file directly to test extraction in isolation
    df = extract()
    print(df.head())
    print(df.columns.tolist())
