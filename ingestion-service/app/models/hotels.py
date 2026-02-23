from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class HotelBase(SQLModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

class Hotel(HotelBase, table=True):
    __tablename__ = "hotels"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class HotelCreate(HotelBase):
    pass

class HotelRead(HotelBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None