from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline.config import (
    AGGREGATED_PARQUET_PATH,
    CLEAN_PARQUET_PATH,
    NORMALIZED_PARQUET_PATH,
    RAW_PARQUET_PATH,
)
from pipeline.kafka_producer import publish_csv_to_topic
from pipeline.kafka_to_parquet import consume_topic_to_parquet
from pipeline.load_star_schema import load_parquet_to_star_schema
from pipeline.spark_jobs import run_aggregate_stage, run_clean_stage, run_normalize_stage


def _cleanup_stage_dirs() -> None:
    for path in [
        RAW_PARQUET_PATH,
        CLEAN_PARQUET_PATH,
        NORMALIZED_PARQUET_PATH,
        AGGREGATED_PARQUET_PATH,
    ]:
        path.mkdir(parents=True, exist_ok=True)


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
}

with DAG(
    dag_id="openaq_etl_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["openaq", "kafka", "spark", "postgres"],
) as dag:
    prepare_dirs = PythonOperator(
        task_id="prepare_stage_dirs",
        python_callable=_cleanup_stage_dirs,
    )

    produce_raw_topic = PythonOperator(
        task_id="produce_raw_topic",
        python_callable=publish_csv_to_topic,
    )

    consume_to_parquet = PythonOperator(
        task_id="consume_to_parquet",
        python_callable=consume_topic_to_parquet,
    )

    clean_stage = PythonOperator(
        task_id="spark_clean_stage",
        python_callable=run_clean_stage,
    )

    normalize_stage = PythonOperator(
        task_id="spark_normalize_stage",
        python_callable=run_normalize_stage,
    )

    aggregate_stage = PythonOperator(
        task_id="spark_aggregate_stage",
        python_callable=run_aggregate_stage,
    )

    load_star_schema = PythonOperator(
        task_id="load_star_schema",
        python_callable=load_parquet_to_star_schema,
    )

    (
        prepare_dirs
        >> produce_raw_topic
        >> consume_to_parquet
        >> clean_stage
        >> normalize_stage
        >> aggregate_stage
        >> load_star_schema
    )
