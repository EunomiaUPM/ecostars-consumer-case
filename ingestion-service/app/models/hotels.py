from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field


class Hotel(SQLModel, table=True):
    __tablename__ = "hotels"

    uuid: UUID = Field(primary_key=True)
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    chain_uuid: Optional[UUID] = Field(default=None, foreign_key="chains.uuid")
    country_slug: Optional[str] = None
    category_slug: Optional[str] = None
    zip: Optional[str] = None
    region: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
