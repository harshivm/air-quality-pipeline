from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from pipeline.config import (
    AGGREGATED_PARQUET_PATH,
    CLEAN_PARQUET_PATH,
    NORMALIZED_PARQUET_PATH,
    RAW_PARQUET_PATH,
)


def _spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def run_clean_stage() -> None:
    spark = _spark("air-quality-clean-stage")
    raw_df = spark.read.parquet(str(RAW_PARQUET_PATH))

    clean_df = (
        raw_df.withColumn("value_num", F.col("Value").cast("double"))
        .withColumn("lat_raw", F.trim(F.split(F.col("Coordinates"), ",").getItem(0)))
        .withColumn("lon_raw", F.trim(F.split(F.col("Coordinates"), ",").getItem(1)))
        .withColumn("latitude", F.col("lat_raw").cast("double"))
        .withColumn("longitude", F.col("lon_raw").cast("double"))
        .withColumn("last_updated", F.to_timestamp(F.col("Last Updated")))
        .select(
            F.col("Country Code").alias("country_code"),
            F.col("City").alias("city"),
            F.col("Location").alias("location"),
            F.col("Pollutant").alias("pollutant"),
            F.col("Source Name").alias("source_name"),
            F.col("Unit").alias("unit"),
            F.col("Country Label").alias("country_label"),
            "latitude",
            "longitude",
            "value_num",
            "last_updated",
        )
        .filter(F.col("pollutant").isNotNull())
        .filter(F.col("value_num").isNotNull())
    )

    clean_df.write.mode("overwrite").parquet(str(CLEAN_PARQUET_PATH))
    spark.stop()


def run_normalize_stage() -> None:
    spark = _spark("air-quality-normalize-stage")
    clean_df = spark.read.parquet(str(CLEAN_PARQUET_PATH))

    normalized_df = (
        clean_df.withColumn("country_code", F.upper(F.trim(F.col("country_code"))))
        .withColumn("city", F.initcap(F.trim(F.col("city"))))
        .withColumn("location", F.trim(F.col("location")))
        .withColumn("pollutant", F.upper(F.trim(F.col("pollutant"))))
        .withColumn("unit", F.trim(F.col("unit")))
        .withColumn("country_label", F.trim(F.col("country_label")))
        .withColumn("measurement_date", F.to_date(F.col("last_updated")))
        .withColumnRenamed("value_num", "value")
        .filter(F.col("measurement_date").isNotNull())
    )

    normalized_df.write.mode("overwrite").parquet(str(NORMALIZED_PARQUET_PATH))
    spark.stop()


def run_aggregate_stage() -> None:
    spark = _spark("air-quality-aggregate-stage")
    normalized_df = spark.read.parquet(str(NORMALIZED_PARQUET_PATH))

    aggregate_df = (
        normalized_df.groupBy(
            "measurement_date",
            "country_code",
            "country_label",
            "city",
            "pollutant",
        )
        .agg(
            F.avg("value").alias("avg_value"),
            F.count(F.lit(1)).alias("record_count"),
        )
        .withColumn("avg_value", F.round(F.col("avg_value"), 4))
    )

    aggregate_df.write.mode("overwrite").parquet(str(AGGREGATED_PARQUET_PATH))
    spark.stop()
