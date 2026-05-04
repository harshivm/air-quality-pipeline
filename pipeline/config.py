import os
from pathlib import Path

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "air_quality_raw")

DATASET_PATH = os.getenv("DATASET_PATH", "/opt/airflow/data/openaq.csv")
STAGING_ROOT = Path(os.getenv("STAGING_ROOT", "/opt/airflow/staging"))

RAW_PARQUET_PATH = STAGING_ROOT / "raw"
CLEAN_PARQUET_PATH = STAGING_ROOT / "clean"
NORMALIZED_PARQUET_PATH = STAGING_ROOT / "normalized"
AGGREGATED_PARQUET_PATH = STAGING_ROOT / "aggregated"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://aqp_user:aqp_pass@db:5432/aqp",
)
