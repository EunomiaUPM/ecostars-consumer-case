import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session

from app.db import get_session
from app.models import Chain, EnvironmentalMetric, Hotel, MetricItem, SocialMetric

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consumer-ingestion", tags=["consumer-ingestion"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PullRequest(BaseModel):
    url: HttpUrl


# ---------------------------------------------------------------------------
# camelCase → snake_case mappings per metric type
# ---------------------------------------------------------------------------

SOCIAL_FIELD_MAP: dict[str, str] = {
    "absenteeismRate": "absenteeism_rate",
    "turnoverRate": "turnover_rate",
    "voluntaryTurnoverRate": "voluntary_turnover_rate",
    "involuntaryTurnoverRate": "involuntary_turnover_rate",
    "retirementTurnoverRate": "retirement_turnover_rate",
    "femaleHeadcountShare": "female_headcount_share",
    "femaleManagementHeadcountShare": "female_management_headcount_share",
    "genderPayGap": "gender_pay_gap",
    "wageInequalityRatio": "wage_inequality_ratio",
    "meanHourlyWage": "mean_hourly_wage",
}

ENVIRONMENTAL_FIELD_MAP: dict[str, str] = {
    "energyTotalKwh": "energy_total_kwh",
    "ratingEnergyRN": "rating_energy_rn",
    "benchmarkRatingEnergyRN": "benchmark_rating_energy_rn",
    "waterM3": "water_m3",
    "ratingWaterRN": "rating_water_rn",
    "benchmarkRatingWaterRN": "benchmark_rating_water_rn",
    "wasteKg": "waste_kg",
    "ratingWasteRN": "rating_waste_rn",
    "benchmarkRatingWasteRN": "benchmark_rating_waste_rn",
    "scope1Emissions": "scope1_emissions",
    "scope2Emissions": "scope2_emissions",
    "scope3Emissions": "scope3_emissions",
    "co2Emissions": "co2_emissions",
    "ratingCO2RN": "rating_co2_rn",
    "benchmarkRatingCO2RN": "benchmark_rating_co2_rn",
}

# Keys that uniquely identify each metric type (present even when null)
_SOCIAL_SENTINEL = "absenteeismRate"
_ENVIRONMENTAL_SENTINEL = "energyTotalKwh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_external_data(url: str) -> list[dict]:
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


def _upsert_chain(session: Session, record: dict, now: datetime) -> str | None:
    if not record.get("chain_uuid"):
        return None

    chain_uuid = UUID(record["chain_uuid"])
    existing = session.get(Chain, chain_uuid)

    if existing:
        existing.name = record.get("chain_name", existing.name)
        existing.updated_at = now
        session.add(existing)
        return "updated"

    session.add(Chain(
        uuid=chain_uuid,
        name=record["chain_name"],
        created_at=now,
        updated_at=now,
    ))
    return "created"


def _upsert_hotel(session: Session, record: dict, now: datetime) -> tuple[Hotel, str]:
    hotel_uuid = UUID(record["hotel_uuid"])
    existing = session.get(Hotel, hotel_uuid)

    chain_uuid = UUID(record["chain_uuid"]) if record.get("chain_uuid") else None

    if existing:
        existing.name = record.get("hotel_name", existing.name)
        existing.lat = record.get("lat", existing.lat)
        existing.lon = record.get("lon", existing.lon)
        existing.chain_uuid = chain_uuid
        existing.country_slug = record.get("country_slug", existing.country_slug)
        existing.category_slug = record.get("category_slug", existing.category_slug)
        existing.zip = record.get("zip", existing.zip)
        existing.region = record.get("region", existing.region)
        existing.updated_at = now
        session.add(existing)
        return existing, "updated"

    hotel = Hotel(
        uuid=hotel_uuid,
        name=record["hotel_name"],
        lat=record.get("lat"),
        lon=record.get("lon"),
        chain_uuid=chain_uuid,
        country_slug=record.get("country_slug"),
        category_slug=record.get("category_slug"),
        zip=record.get("zip"),
        region=record.get("region"),
        created_at=now,
        updated_at=now,
    )
    session.add(hotel)
    session.flush()
    return hotel, "created"


def _upsert_social_metric(
    session: Session,
    hotel_uuid: UUID,
    raw: dict,
    now: datetime,
) -> str:
    metric_uuid = UUID(raw["uuid"])
    existing = session.get(SocialMetric, metric_uuid)

    if existing:
        for camel, snake in SOCIAL_FIELD_MAP.items():
            if camel in raw:
                setattr(existing, snake, raw[camel])
        existing.updated_at = now
        session.add(existing)
        return "updated"

    session.add(SocialMetric(
        uuid=metric_uuid,
        hotel_uuid=hotel_uuid,
        periodicity=raw["periodicity"],
        period=raw["period"],
        absenteeism_rate=raw.get("absenteeismRate"),
        turnover_rate=raw.get("turnoverRate"),
        voluntary_turnover_rate=raw.get("voluntaryTurnoverRate"),
        involuntary_turnover_rate=raw.get("involuntaryTurnoverRate"),
        retirement_turnover_rate=raw.get("retirementTurnoverRate"),
        female_headcount_share=raw.get("femaleHeadcountShare"),
        female_management_headcount_share=raw.get("femaleManagementHeadcountShare"),
        gender_pay_gap=raw.get("genderPayGap"),
        wage_inequality_ratio=raw.get("wageInequalityRatio"),
        mean_hourly_wage=raw.get("meanHourlyWage"),
        created_at=now,
        updated_at=now,
    ))
    return "created"


def _upsert_environmental_metric(
    session: Session,
    hotel_uuid: UUID,
    raw: dict,
    now: datetime,
) -> str:
    metric_uuid = UUID(raw["uuid"])
    existing = session.get(EnvironmentalMetric, metric_uuid)

    if existing:
        for camel, snake in ENVIRONMENTAL_FIELD_MAP.items():
            if camel in raw:
                setattr(existing, snake, raw[camel])
        existing.updated_at = now
        session.add(existing)
        return "updated"

    session.add(EnvironmentalMetric(
        uuid=metric_uuid,
        hotel_uuid=hotel_uuid,
        periodicity=raw["periodicity"],
        period=raw["period"],
        energy_total_kwh=raw.get("energyTotalKwh"),
        rating_energy_rn=raw.get("ratingEnergyRN"),
        benchmark_rating_energy_rn=raw.get("benchmarkRatingEnergyRN"),
        water_m3=raw.get("waterM3"),
        rating_water_rn=raw.get("ratingWaterRN"),
        benchmark_rating_water_rn=raw.get("benchmarkRatingWaterRN"),
        waste_kg=raw.get("wasteKg"),
        rating_waste_rn=raw.get("ratingWasteRN"),
        benchmark_rating_waste_rn=raw.get("benchmarkRatingWasteRN"),
        scope1_emissions=raw.get("scope1Emissions"),
        scope2_emissions=raw.get("scope2Emissions"),
        scope3_emissions=raw.get("scope3Emissions"),
        co2_emissions=raw.get("co2Emissions"),
        rating_co2_rn=raw.get("ratingCO2RN"),
        benchmark_rating_co2_rn=raw.get("benchmarkRatingCO2RN"),
        created_at=now,
        updated_at=now,
    ))
    return "created"


def _upsert_metric(
    session: Session,
    hotel_uuid: UUID,
    raw: dict,
    now: datetime,
) -> tuple[str, str]:
    """Route a value record to the correct metric table by inspecting its keys."""
    if _ENVIRONMENTAL_SENTINEL in raw:
        action = _upsert_environmental_metric(session, hotel_uuid, raw, now)
        return "environmental", action
    action = _upsert_social_metric(session, hotel_uuid, raw, now)
    return "social", action


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/pull", status_code=status.HTTP_200_OK)
def get_bulk_data(
    body: PullRequest,
    session: Session = Depends(get_session),
) -> Any:
    """
    Fetches hotel data from an external URL and persists it.
    Chains and hotels are upserted by UUID. Social metrics are upserted by UUID.
    """
    records = _fetch_external_data(str(body.url))
    logger.info("[/pull] Fetched %d records from %s", len(records), body.url)

    now = datetime.utcnow()
    summary: dict[str, int] = {
        "chains_created": 0,
        "chains_updated": 0,
        "hotels_created": 0,
        "hotels_updated": 0,
        "social_metrics_created": 0,
        "social_metrics_updated": 0,
        "environmental_metrics_created": 0,
        "environmental_metrics_updated": 0,
    }

    for record in records:
        chain_action = _upsert_chain(session, record, now)
        if chain_action:
            summary[f"chains_{chain_action}"] += 1

        hotel, hotel_action = _upsert_hotel(session, record, now)
        summary[f"hotels_{hotel_action}"] += 1

        with session.no_autoflush:
            for raw_metric in record.get("values", []):
                metric_type, metric_action = _upsert_metric(session, hotel.uuid, raw_metric, now)
                summary[f"{metric_type}_metrics_{metric_action}"] += 1

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
    """
    payload = await request.json()
    logger.info("[/push] Received payload: %s", payload)

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
