import csv
import json
from pathlib import Path

from kafka import KafkaProducer

from pipeline.config import DATASET_PATH, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def publish_csv_to_topic(path: str | None = None, topic: str | None = None) -> int:
    source = Path(path or DATASET_PATH)
    if not source.exists():
        raise FileNotFoundError(f"CSV source not found: {source}")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
    )

    count = 0
    with source.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for row in reader:
            producer.send(topic or KAFKA_TOPIC, value=row)
            count += 1

    producer.flush()
    producer.close()
    print(f"Published {count} messages to topic '{topic or KAFKA_TOPIC}'.")
    return count


if __name__ == "__main__":
    publish_csv_to_topic()
