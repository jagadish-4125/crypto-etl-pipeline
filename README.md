# Crypto Market ETL Pipeline

A complete, production-style ETL (Extract, Transform, Load) pipeline that pulls
live cryptocurrency market data from the **CoinGecko public API** and loads it
into a **PostgreSQL** database, with upsert logic, historical snapshotting,
logging, and retry/backoff handling.

## Architecture

```
CoinGecko API  --->  EXTRACT  --->  TRANSFORM  --->  LOAD  --->  PostgreSQL
                    (requests)      (pandas)      (SQLAlchemy)
```

```
etl_project/
├── main.py                 # Orchestrates the full pipeline
├── requirements.txt
├── .env.example             # Template for your DB credentials
├── config/
│   └── config.py           # Loads settings from .env
├── src/
│   ├── extract.py          # Pulls data from CoinGecko API (with retries)
│   ├── transform.py        # Cleans, types, and enriches the data
│   ├── load.py              # Upserts into PostgreSQL
│   └── logger.py           # Centralized logging setup
├── sql/
│   └── schema.sql          # Target table DDL
└── logs/                    # Auto-generated daily log files
```

## What it does

1. **Extract** — Calls CoinGecko's `/coins/markets` endpoint to fetch the top
   100 cryptocurrencies by market cap. Handles HTTP errors, rate limiting
   (429s), and retries with backoff.
2. **Transform** — Selects relevant fields, renames them to clean snake_case,
   fixes data types, fills missing values, and adds **derived columns**:
   - `volume_to_market_cap_ratio`
   - `price_range_24h`
   - `is_near_ath` (within 10% of all-time high)
   - `etl_loaded_at` (audit timestamp)
3. **Load** — Connects to PostgreSQL and:
   - Creates the schema automatically if it doesn't exist
   - **Upserts** into `crypto_market_data` (updates existing coins, inserts new ones)
   - Appends a snapshot into `crypto_market_data_history` so you can track price
     changes across multiple pipeline runs over time

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your database
Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```bash
cp .env.example .env
```

### 3. Run the pipeline
```bash
python main.py
```

That's it — the script creates the tables for you on first run.

## Re-running the pipeline

Run it again any time (e.g. on a schedule with `cron` or Airflow) — it will:
- Update existing coin rows with fresh prices (upsert, no duplicates)
- Add a new row per coin into the history table, so you build up a time series

## Possible extensions (good for your portfolio narrative)

- Schedule with `cron` or Apache Airflow for hourly runs
- Add a Slack/email alert when a coin moves >10% in 24h
- Build a small dashboard (Streamlit/Metabase) on top of the history table
- Containerize with Docker + docker-compose (Postgres + pipeline in one stack)
- Add unit tests with `pytest` for the transform logic
