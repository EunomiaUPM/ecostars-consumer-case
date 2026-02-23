from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class HotelEventModelBase(SQLModel):
    hotel_id: Optional[int] = Field(default=None, foreign_key="hotels.id")
    event_name: Optional[str] = None
    event_content: Optional[str] = None

class HotelEventModel(HotelEventModelBase, table=True):
    __tablename__ = "hotel_even_models"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class HotelEventModelCreate(HotelEventModelBase):
    pass

class HotelEventModelRead(HotelEventModelBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None