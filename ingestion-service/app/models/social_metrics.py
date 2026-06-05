from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field


class SocialMetric(SQLModel, table=True):
    __tablename__ = "social_metrics"

    uuid: UUID = Field(primary_key=True)
    hotel_uuid: UUID = Field(foreign_key="hotels.uuid")
    periodicity: str
    period: str  # PostgreSQL daterange notation e.g. "[2023-01-01,2024-01-01)"
    absenteeism_rate: Optional[float] = None
    turnover_rate: Optional[float] = None
    voluntary_turnover_rate: Optional[float] = None
    involuntary_turnover_rate: Optional[float] = None
    retirement_turnover_rate: Optional[float] = None
    female_headcount_share: Optional[float] = None
    female_management_headcount_share: Optional[float] = None
    gender_pay_gap: Optional[float] = None
    wage_inequality_ratio: Optional[float] = None
    mean_hourly_wage: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
