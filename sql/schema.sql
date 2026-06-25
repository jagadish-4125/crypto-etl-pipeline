-- schema.sql
-- Creates the target table that the ETL pipeline loads data into.
-- Run this once manually, OR let load.py auto-create it on first run.

CREATE TABLE IF NOT EXISTS crypto_market_data (
    coin_id                     VARCHAR(100) PRIMARY KEY,
    symbol                       VARCHAR(20),
    name                         VARCHAR(100),
    current_price                NUMERIC(20, 6),
    market_cap                   NUMERIC(30, 2),
    market_cap_rank              INTEGER,
    total_volume                 NUMERIC(30, 2),
    high_24h                     NUMERIC(20, 6),
    low_24h                      NUMERIC(20, 6),
    price_change_24h             NUMERIC(20, 6),
    price_change_pct_24h         NUMERIC(10, 4),
    price_change_pct_7d          NUMERIC(10, 4),
    circulating_supply           NUMERIC(30, 4),
    total_supply                 NUMERIC(30, 4),
    all_time_high                NUMERIC(20, 6),
    pct_from_ath                 NUMERIC(10, 4),
    api_last_updated              TIMESTAMPTZ,
    volume_to_market_cap_ratio    NUMERIC(10, 4),
    price_range_24h              NUMERIC(20, 6),
    is_near_ath                  BOOLEAN,
    etl_loaded_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index to speed up common queries (e.g. filtering/sorting by rank)
CREATE INDEX IF NOT EXISTS idx_market_cap_rank ON crypto_market_data (market_cap_rank);

-- Optional: a history table if you want to track changes over time
-- instead of overwriting each run (see load.py LOAD_MODE="append")
CREATE TABLE IF NOT EXISTS crypto_market_data_history (
    id                           SERIAL PRIMARY KEY,
    coin_id                      VARCHAR(100),
    symbol                       VARCHAR(20),
    name                          VARCHAR(100),
    current_price                NUMERIC(20, 6),
    market_cap                   NUMERIC(30, 2),
    market_cap_rank              INTEGER,
    total_volume                 NUMERIC(30, 2),
    price_change_pct_24h         NUMERIC(10, 4),
    etl_loaded_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
