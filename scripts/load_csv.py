import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import insert

from app.database import SessionLocal, wait_for_db
from app.models import Measurement


def parse_coordinates(raw: str | None) -> tuple[float | None, float | None]:
    if not raw:
        return None, None

    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        return None, None

    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def parse_datetime(raw: str | None):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def normalize(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text if text else None


def row_to_record(row: dict) -> dict:
    latitude, longitude = parse_coordinates(row.get("Coordinates"))

    value_raw = normalize(row.get("Value"))
    try:
        numeric_value = float(value_raw) if value_raw is not None else None
    except ValueError:
        numeric_value = None

    return {
        "country_code": normalize(row.get("Country Code")),
        "city": normalize(row.get("City")),
        "location": normalize(row.get("Location")),
        "latitude": latitude,
        "longitude": longitude,
        "pollutant": normalize(row.get("Pollutant")) or "UNKNOWN",
        "source_name": normalize(row.get("Source Name")),
        "unit": normalize(row.get("Unit")),
        "value": numeric_value,
        "last_updated": parse_datetime(normalize(row.get("Last Updated"))),
        "country_label": normalize(row.get("Country Label")),
    }


def load_csv(path: str, chunk_size: int = 5000) -> int:
    wait_for_db()
    total = 0
    batch: list[dict] = []

    with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        with SessionLocal() as session:
            for row in reader:
                batch.append(row_to_record(row))
                if len(batch) >= chunk_size:
                    session.execute(insert(Measurement), batch)
                    session.commit()
                    total += len(batch)
                    batch.clear()

            if batch:
                session.execute(insert(Measurement), batch)
                session.commit()
                total += len(batch)

    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Load OpenAQ CSV data into PostgreSQL")
    parser.add_argument("--path", required=True, help="Path to semicolon-delimited OpenAQ CSV file")
    args = parser.parse_args()

    total = load_csv(path=args.path)
    print(f"Loaded {total} rows from {args.path}")


if __name__ == "__main__":
    main()
