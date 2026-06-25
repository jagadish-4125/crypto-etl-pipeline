"""
main.py
-------
Orchestrates the full ETL pipeline: Extract -> Transform -> Load.

Run this file to execute the entire pipeline end-to-end:
    python main.py
"""

import sys
import os
import time

sys.path.append(os.path.dirname(__file__))

from src.extract import extract
from src.transform import transform
from src.load import load
from src.logger import get_logger

logger = get_logger("PIPELINE")


def run_pipeline():
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("STARTING ETL PIPELINE: Cryptocurrency Market Data")
    logger.info("=" * 60)

    try:
        # ----- EXTRACT -----
        logger.info("STEP 1/3: EXTRACT")
        raw_df = extract()

        # ----- TRANSFORM -----
        logger.info("STEP 2/3: TRANSFORM")
        clean_df = transform(raw_df)

        # ----- LOAD -----
        logger.info("STEP 3/3: LOAD")
        load(clean_df)

        elapsed = round(time.time() - start_time, 2)
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY in {elapsed}s")
        logger.info(f"Rows processed: {len(clean_df)}")
        logger.info("=" * 60)

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logger.critical(f"PIPELINE FAILED after {elapsed}s: {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
