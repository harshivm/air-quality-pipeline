from pathlib import Path

from fastapi import Depends, FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

app = FastAPI(title="Air Quality Project API", version="1.0.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/records", response_model=list[schemas.MeasurementOut])
def get_records(
    pollutant: str | None = Query(default=None),
    country_code: str | None = Query(default=None),
    city: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_measurements(
        db=db,
        pollutant=pollutant,
        country_code=country_code,
        city=city,
        limit=limit,
        offset=offset,
    )


@app.get("/summary", response_model=schemas.SummaryOut)
def get_summary(db: Session = Depends(get_db)):
    return crud.build_summary(db)
