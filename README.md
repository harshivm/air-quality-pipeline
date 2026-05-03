# Air Quality Project (Kafka + Spark + Airflow)

This implementation now includes the full architecture:
- OpenAQ CSV data source
- Kafka broker with air_quality_raw topic
- Parquet staging volume
- Spark batch ETL in 3 stages (clean, normalize, aggregate)
- PostgreSQL star schema (dimensions + fact)
- Airflow orchestration inside Docker Compose
- FastAPI dashboard and API

## Dataset
- CSV path in workspace: data/openaq.csv
- Expected delimiter: semicolon (;)
- Expected headers:
  - Country Code
  - City
  - Location
  - Coordinates
  - Pollutant
  - Source Name
  - Unit
  - Value
  - Last Updated
  - Country Label

## Architecture Flow
1. Source CSV data is published to Kafka topic air_quality_raw.
2. Kafka messages are consumed into raw Parquet staging.
3. Spark clean stage filters/parses records into clean Parquet.
4. Spark normalize stage standardizes values and creates measurement date.
5. Spark aggregate stage computes grouped metrics.
6. Loader writes dimension and fact tables to PostgreSQL star schema.
7. FastAPI serves API and dashboard output.

## Run With Docker Compose
1. Copy environment file:
   - PowerShell: Copy-Item .env.example .env
2. Start infrastructure and app:
   - docker compose up -d db kafka kafka-init airflow app
3. Trigger Airflow DAG (Kafka -> Parquet -> Spark -> Star Schema):
   - docker compose exec airflow airflow dags trigger openaq_etl_pipeline
4. Optionally watch DAG/task status:
   - docker compose exec airflow airflow dags list-runs -d openaq_etl_pipeline
   - docker compose exec airflow airflow tasks list openaq_etl_pipeline

## Service URLs
- FastAPI dashboard: http://localhost:8000/
- FastAPI docs: http://localhost:8000/docs
- Airflow UI: http://localhost:8080

## API Endpoints
- GET /
- GET /health
- GET /summary
- GET /records?pollutant=NO2&country_code=BE&city=Brussels&limit=100&offset=0

## Star Schema Tables (PostgreSQL)
- dim_date
- dim_location
- dim_pollutant
- fact_air_quality

The pipeline also refreshes a measurements snapshot table for dashboard/API compatibility.

## Dashboard Output
- KPI cards for record/pollutant/country counts
- Top pollutant and country bars
- Filterable table of recent records

## Stop Stack
- docker compose down

## Notes
- If port 5432 is busy on host, DB is already mapped to host port 5433 by default.
- Kafka and Airflow run inside Compose; no separate local installs are required.
