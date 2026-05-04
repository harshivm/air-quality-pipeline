from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from pipeline.config import AGGREGATED_PARQUET_PATH, DATABASE_URL, NORMALIZED_PARQUET_PATH


def _ensure_schema(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS dim_date (
                id SERIAL PRIMARY KEY,
                full_date DATE NOT NULL UNIQUE,
                year INT NOT NULL,
                month INT NOT NULL,
                day INT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dim_location (
                id SERIAL PRIMARY KEY,
                country_code VARCHAR(8),
                country_label VARCHAR(128),
                city VARCHAR(128),
                UNIQUE(country_code, country_label, city)
            );

            CREATE TABLE IF NOT EXISTS dim_pollutant (
                id SERIAL PRIMARY KEY,
                pollutant_code VARCHAR(16) NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS fact_air_quality (
                id BIGSERIAL PRIMARY KEY,
                date_id INT NOT NULL REFERENCES dim_date(id),
                location_id INT NOT NULL REFERENCES dim_location(id),
                pollutant_id INT NOT NULL REFERENCES dim_pollutant(id),
                avg_value DOUBLE PRECISION NOT NULL,
                record_count INT NOT NULL,
                UNIQUE(date_id, location_id, pollutant_id)
            );

            CREATE TABLE IF NOT EXISTS measurements (
                id BIGSERIAL PRIMARY KEY,
                country_code VARCHAR(8),
                city VARCHAR(128),
                location VARCHAR(256),
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                pollutant VARCHAR(16),
                source_name VARCHAR(128),
                unit VARCHAR(32),
                value DOUBLE PRECISION,
                last_updated TIMESTAMPTZ,
                country_label VARCHAR(128)
            );
            """
        )
    )


def _get_or_create_date(conn, date_value):
    conn.execute(
        text(
            """
            INSERT INTO dim_date(full_date, year, month, day)
            VALUES (:full_date, :year, :month, :day)
            ON CONFLICT (full_date) DO NOTHING
            """
        ),
        {
            "full_date": date_value,
            "year": date_value.year,
            "month": date_value.month,
            "day": date_value.day,
        },
    )
    return conn.execute(
        text("SELECT id FROM dim_date WHERE full_date = :full_date"),
        {"full_date": date_value},
    ).scalar_one()


def _get_or_create_location(conn, country_code, country_label, city):
    conn.execute(
        text(
            """
            INSERT INTO dim_location(country_code, country_label, city)
            VALUES (:country_code, :country_label, :city)
            ON CONFLICT (country_code, country_label, city) DO NOTHING
            """
        ),
        {
            "country_code": country_code,
            "country_label": country_label,
            "city": city,
        },
    )
    return conn.execute(
        text(
            """
            SELECT id FROM dim_location
            WHERE country_code = :country_code
              AND country_label = :country_label
              AND city = :city
            """
        ),
        {
            "country_code": country_code,
            "country_label": country_label,
            "city": city,
        },
    ).scalar_one()


def _get_or_create_pollutant(conn, pollutant_code):
    conn.execute(
        text(
            """
            INSERT INTO dim_pollutant(pollutant_code)
            VALUES (:pollutant_code)
            ON CONFLICT (pollutant_code) DO NOTHING
            """
        ),
        {"pollutant_code": pollutant_code},
    )
    return conn.execute(
        text("SELECT id FROM dim_pollutant WHERE pollutant_code = :pollutant_code"),
        {"pollutant_code": pollutant_code},
    ).scalar_one()


def _load_measurements_snapshot(conn, normalized_path: Path) -> int:
    if not normalized_path.exists():
        return 0

    df = pd.read_parquet(normalized_path)
    if df.empty:
        return 0

    conn.execute(text("TRUNCATE TABLE measurements"))
    rows = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "country_code": row.get("country_code"),
                "city": row.get("city"),
                "location": row.get("location"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "pollutant": row.get("pollutant"),
                "source_name": row.get("source_name"),
                "unit": row.get("unit"),
                "value": row.get("value"),
                "last_updated": row.get("last_updated"),
                "country_label": row.get("country_label"),
            }
        )

    conn.execute(
        text(
            """
            INSERT INTO measurements(
                country_code, city, location, latitude, longitude,
                pollutant, source_name, unit, value, last_updated, country_label
            ) VALUES (
                :country_code, :city, :location, :latitude, :longitude,
                :pollutant, :source_name, :unit, :value, :last_updated, :country_label
            )
            """
        ),
        rows,
    )
    return len(rows)


def load_parquet_to_star_schema(aggregated_path: str | None = None) -> int:
    source = Path(aggregated_path) if aggregated_path else AGGREGATED_PARQUET_PATH
    if not source.exists():
        raise FileNotFoundError(f"Aggregated parquet path not found: {source}")

    df = pd.read_parquet(source)
    if df.empty:
        raise RuntimeError("Aggregated parquet dataset is empty.")

    engine = create_engine(DATABASE_URL)
    loaded = 0

    with engine.begin() as conn:
        _ensure_schema(conn)

        for row in df.to_dict(orient="records"):
            date_id = _get_or_create_date(conn, row["measurement_date"])
            location_id = _get_or_create_location(
                conn,
                row.get("country_code"),
                row.get("country_label"),
                row.get("city"),
            )
            pollutant_id = _get_or_create_pollutant(conn, row["pollutant"])

            conn.execute(
                text(
                    """
                    INSERT INTO fact_air_quality(
                        date_id, location_id, pollutant_id, avg_value, record_count
                    ) VALUES (
                        :date_id, :location_id, :pollutant_id, :avg_value, :record_count
                    )
                    ON CONFLICT (date_id, location_id, pollutant_id)
                    DO UPDATE SET
                        avg_value = EXCLUDED.avg_value,
                        record_count = EXCLUDED.record_count
                    """
                ),
                {
                    "date_id": date_id,
                    "location_id": location_id,
                    "pollutant_id": pollutant_id,
                    "avg_value": float(row["avg_value"]),
                    "record_count": int(row["record_count"]),
                },
            )
            loaded += 1

        measurements_loaded = _load_measurements_snapshot(conn, NORMALIZED_PARQUET_PATH)

    print(f"Loaded {loaded} aggregated rows into star schema.")
    print(f"Loaded {measurements_loaded} rows into measurements snapshot.")
    return loaded


if __name__ == "__main__":
    load_parquet_to_star_schema()
