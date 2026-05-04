from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_code: str | None
    city: str | None
    location: str | None
    latitude: float | None
    longitude: float | None
    pollutant: str
    source_name: str | None
    unit: str | None
    value: float | None
    last_updated: datetime | None
    country_label: str | None


class SummaryOut(BaseModel):
    total_records: int
    pollutants: dict[str, int]
    countries: dict[str, int]
