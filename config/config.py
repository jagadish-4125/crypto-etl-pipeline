"""
config.py
----------
Centralized configuration loader. Reads all settings from environment
variables (via a .env file) so credentials never get hardcoded into
the codebase. This is standard practice in real ETL pipelines.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()


class Config:
    # --- PostgreSQL connection settings ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "crypto_etl")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # --- API settings ---
    API_BASE_URL = os.getenv("API_BASE_URL", "https://api.coingecko.com/api/v3")
    API_CURRENCY = os.getenv("API_CURRENCY", "usd")
    API_TOP_N_COINS = int(os.getenv("API_TOP_N_COINS", 100))

    @classmethod
    def get_db_connection_string(cls):
        """Builds a SQLAlchemy-style connection string."""
        return (
            f"postgresql+psycopg2://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    @classmethod
    def get_psycopg2_conn_params(cls):
        """Builds a dict of connection params for raw psycopg2 connections."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "dbname": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
        }
