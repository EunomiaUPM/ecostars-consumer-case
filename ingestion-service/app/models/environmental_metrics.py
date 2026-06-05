from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field


class EnvironmentalMetric(SQLModel, table=True):
    __tablename__ = "environmental_metrics"

    uuid: UUID = Field(primary_key=True)
    hotel_uuid: UUID = Field(foreign_key="hotels.uuid")
    periodicity: str
    period: str  # PostgreSQL daterange notation e.g. "[2023-01-01,2024-01-01)"
    energy_total_kwh: Optional[float] = None
    rating_energy_rn: Optional[float] = None
    benchmark_rating_energy_rn: Optional[float] = None
    water_m3: Optional[float] = None
    rating_water_rn: Optional[float] = None
    benchmark_rating_water_rn: Optional[float] = None
    waste_kg: Optional[float] = None
    rating_waste_rn: Optional[float] = None
    benchmark_rating_waste_rn: Optional[float] = None
    scope1_emissions: Optional[float] = None
    scope2_emissions: Optional[float] = None
    scope3_emissions: Optional[float] = None
    co2_emissions: Optional[float] = None
    rating_co2_rn: Optional[float] = None
    benchmark_rating_co2_rn: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
