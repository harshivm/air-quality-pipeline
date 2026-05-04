import json
import time
from pathlib import Path

import pandas as pd
from kafka import KafkaConsumer

from pipeline.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, RAW_PARQUET_PATH


def consume_topic_to_parquet(
    output_path: str | None = None,
    topic: str | None = None,
    idle_timeout_seconds: int = 8,
) -> int:
    target = Path(output_path) if output_path else RAW_PARQUET_PATH
    target.mkdir(parents=True, exist_ok=True)

    consumer = KafkaConsumer(
        topic or KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=f"airflow-batch-{int(time.time())}",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=1000,
    )

    records: list[dict] = []
    idle_seconds = 0

    while idle_seconds < idle_timeout_seconds:
        batch_seen = False
        for message in consumer:
            records.append(message.value)
            batch_seen = True
        if batch_seen:
            idle_seconds = 0
        else:
            idle_seconds += 1

    consumer.close()

    if not records:
        raise RuntimeError("No Kafka messages were consumed from topic.")

    df = pd.DataFrame(records)
    parquet_file = target / "part-00000.parquet"
    df.to_parquet(parquet_file, index=False)
    print(f"Wrote {len(records)} records to {parquet_file}")
    return len(records)


if __name__ == "__main__":
    consume_topic_to_parquet()
