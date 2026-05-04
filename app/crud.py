from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Measurement


def list_measurements(
    db: Session,
    pollutant: str | None = None,
    country_code: str | None = None,
    city: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(Measurement)

    if pollutant:
        query = query.filter(Measurement.pollutant == pollutant)
    if country_code:
        query = query.filter(Measurement.country_code == country_code)
    if city:
        query = query.filter(Measurement.city == city)

    return query.order_by(Measurement.last_updated.desc().nullslast()).offset(offset).limit(limit).all()


def build_summary(db: Session) -> dict:
    total_records = db.query(func.count(Measurement.id)).scalar() or 0

    pollutant_rows = (
        db.query(Measurement.pollutant, func.count(Measurement.id))
        .group_by(Measurement.pollutant)
        .all()
    )
    country_rows = (
        db.query(Measurement.country_label, func.count(Measurement.id))
        .group_by(Measurement.country_label)
        .all()
    )

    return {
        "total_records": int(total_records),
        "pollutants": {str(k): int(v) for k, v in pollutant_rows if k},
        "countries": {str(k): int(v) for k, v in country_rows if k},
    }
