import logging
from datetime import date, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session, select

from app.db import get_session
from app.models import Hotel, HotelMeasure, MetricItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consumer-ingestion", tags=["consumer-ingestion"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PullRequest(BaseModel):
    url: HttpUrl


# ---------------------------------------------------------------------------
# camelCase → snake_case field mapping for HotelMeasure payloads.
# The external API returns measure fields in camelCase; our DB columns use
# snake_case. Any key not present in this map falls back to key.lower().
# ---------------------------------------------------------------------------

MEASURES_FIELD_MAP: dict[str, str] = {
    "gasKwh": "gas_kwh",
    "waterM3": "water_m3",
    "energyKwh": "energy_kwh",
    "ratingCo2": "rating_co2",
    "totalArea": "total_area",
    "staysPerRN": "stays_per_rn",
    "ratingCo2RN": "rating_co2_rn",
    "ratingWater": "rating_water",
    "deviationCo2": "deviation_co2",
    "ratingEnergy": "rating_energy",
    "ratingCo2S1RN": "rating_co2_s1_rn",
    "ratingCo2S2RN": "rating_co2_s2_rn",
    "ratingCo2Stay": "rating_co2_stay",
    "ratingWaterRN": "rating_water_rn",
    "deviationCo2RN": "deviation_co2_rn",
    "deviationWaste": "deviation_waste",
    "deviationWater": "deviation_water",
    "electricityKwh": "electricity_kwh",
    "ratingEnergyRN": "rating_energy_rn",
    "totalEmissions": "total_emissions",
    "co2Compensation": "co2_compensation",
    "deviationEnergy": "deviation_energy",
    "ratingCo2S1Stay": "rating_co2_s1_stay",
    "ratingCo2S2Stay": "rating_co2_s2_stay",
    "ratingWaterArea": "rating_water_area",
    "ratingWaterRoom": "rating_water_room",
    "ratingWaterStay": "rating_water_stay",
    "scope1Emissions": "scope1_emissions",
    "scope2Emissions": "scope2_emissions",
    "deviationCo2S1RN": "deviation_co2_s1_rn",
    "deviationCo2S2RN": "deviation_co2_s2_rn",
    "deviationCo2S3RN": "deviation_co2_s3_rn",
    "deviationCo2Stay": "deviation_co2_stay",
    "deviationWasteRN": "deviation_waste_rn",
    "deviationWaterRN": "deviation_water_rn",
    "directStationary": "direct_stationary",
    "ratingEnergyArea": "rating_energy_area",
    "ratingEnergyRoom": "rating_energy_room",
    "ratingEnergyStay": "rating_energy_stay",
    "recommendedStars": "recommended_stars",
    "deviationEnergyRN": "deviation_energy_rn",
    "deviationCo2S1Stay": "deviation_co2_s1_stay",
    "deviationCo2S2Stay": "deviation_co2_s2_stay",
    "deviationCo2S3Stay": "deviation_co2_s3_stay",
    "deviationWasteStay": "deviation_waste_stay",
    "deviationWaterStay": "deviation_water_stay",
    "recommendedStarsV1": "recommended_stars_v1",
    "recommendedStarsV2": "recommended_stars_v2",
    "scope2Compensation": "scope2_compensation",
    "deviationEnergyStay": "deviation_energy_stay",
    "energyKwhWithCo2Compensation": "energy_kwh_with_co2_compensation",
    "ratingEnergyWithCo2Compensation": "rating_energy_with_co2_compensation",
    "deviationEnergyWithCo2Compensation": "deviation_energy_with_co2_compensation",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_measure(raw: dict) -> dict:
    """Translate a raw measure dict from camelCase to snake_case column names."""
    return {MEASURES_FIELD_MAP.get(k, k.lower()): v for k, v in raw.items()}


def _fetch_external_data(url: str) -> list[dict]:
    """
    Perform a synchronous GET request to the external URL and return the
    payload normalised as a list (handles both single-object and list responses).
    Raises HTTPException on network or HTTP errors.
    """
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout connecting to {url}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External URL returned {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Connection error: {exc}",
        )

    payload = response.json()
    return payload if isinstance(payload, list) else [payload]


def _upsert_hotel(session: Session, record: dict, now: datetime) -> tuple[Hotel, str]:
    """
    Insert or update a Hotel row identified by (name, city).
    Returns the Hotel instance and the action performed ("created" | "updated").
    """
    hotel = session.exec(
        select(Hotel).where(
            Hotel.name == record.get("name"),
            Hotel.city == record.get("city"),
            Hotel.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()

    if hotel:
        hotel.address = record.get("address", hotel.address)
        hotel.updated_at = now
        session.add(hotel)
        return hotel, "updated"

    hotel = Hotel(
        name=record.get("name"),
        address=record.get("address"),
        city=record.get("city"),
        created_at=now,
        updated_at=now,
    )
    session.add(hotel)
    session.flush()  # materialise hotel.id before processing its measures
    return hotel, "created"


def _upsert_measure(
    session: Session,
    hotel: Hotel,
    raw_measure: dict,
    now: datetime,
) -> str:
    """
    Insert or update a HotelMeasure row identified by (hotel_id, year).
    Returns the action performed ("created" | "updated").

    The external hotel_id is intentionally ignored; we always use the local
    hotel.id to maintain referential integrity.
    """
    normalized = _normalize_measure(raw_measure)
    year = normalized.get("year")

    if year is None:
        return "skipped"

    existing = session.exec(
        select(HotelMeasure).where(
            HotelMeasure.hotel_id == hotel.id,
            HotelMeasure.year == year,
            HotelMeasure.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()

    # Fields that must never be overwritten from the external payload
    PROTECTED_FIELDS = {"id", "created_at", "hotel_id"}

    if existing:
        for key, value in normalized.items():
            if hasattr(existing, key) and key not in PROTECTED_FIELDS:
                setattr(existing, key, value)
        existing.updated_at = now
        session.add(existing)
        return "updated"

    measure_data = {
        k: v
        for k, v in normalized.items()
        if hasattr(HotelMeasure, k) and k not in PROTECTED_FIELDS
    }
    session.add(HotelMeasure(**measure_data, hotel_id=hotel.id, created_at=now, updated_at=now))
    return "created"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/pull", status_code=status.HTTP_200_OK)
def get_bulk_data(
    body: PullRequest,
    session: Session = Depends(get_session),
) -> Any:
    """
    Trigger endpoint that fetches hotel data from an external URL and persists
    it locally. Hotels are upserted by (name, city); their nested measures are
    upserted by (hotel_id, year). Returns a summary of the operations performed.
    """
    records = _fetch_external_data(str(body.url))
    logger.info("[/pull] Fetched %d records from %s", len(records), body.url)

    now = datetime.utcnow()
    summary: dict[str, int] = {
        "hotels_created": 0,
        "hotels_updated": 0,
        "measures_created": 0,
        "measures_updated": 0,
        "measures_skipped": 0,
    }

    for record in records:
        hotel, hotel_action = _upsert_hotel(session, record, now)
        summary[f"hotels_{hotel_action}"] += 1

        # Disable autoflush while iterating measures to avoid premature FK checks
        # before the parent hotel row has been committed.
        with session.no_autoflush:
            for raw_measure in record.get("measures", []):
                measure_action = _upsert_measure(session, hotel, raw_measure, now)
                summary[f"measures_{measure_action}"] += 1

    session.commit()
    logger.info("[/pull] Done. Summary: %s", summary)

    return {"source": str(body.url), "total_received": len(records), "summary": summary}


@router.post("/push", status_code=status.HTTP_201_CREATED)
async def listen_to_changes(
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    """
    Webhook endpoint that receives real-time metric updates and appends them
    to the metric_items table as immutable historical records.

    The incoming `id` field is treated as an external hotel identifier and
    stored as-is in hotel_id (no FK validation against the hotels table).
    """
    payload = await request.json()
    logger.info("[/push] Received payload: %s", payload)

    # Parse ISO-8601 date string (e.g. "2026-02-23T00:00:00Z") to a date object
    last_measured_at: date = datetime.fromisoformat(
        payload["last_measured_at"].replace("Z", "+00:00")
    ).date()

    now = datetime.utcnow()

    item = MetricItem(
        hotel_id=payload["id"],
        item_type=payload["item_type"],
        last_value=payload["last_value"],
        last_measured_at=last_measured_at,
        created_at=now,
        updated_at=now,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info("[/push] Inserted metric_item id=%d for hotel_id=%d", item.id, item.hotel_id)

    return {
        "action": "created",
        "id": item.id,
        "hotel_id": item.hotel_id,
        "item_type": item.item_type,
        "last_value": item.last_value,
        "last_measured_at": str(item.last_measured_at),
    }