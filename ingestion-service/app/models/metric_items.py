from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field



class MetricItemBase(SQLModel):
    hotel_id: int  # id externo, sin FK
    item_type: str = Field(max_length=50)
    last_value: float
    last_measured_at: date

class MetricItem(MetricItemBase, table=True):
    __tablename__ = "metric_items"

    id: Optional[int] = Field(default=None, primary_key=True)  # autoincremental
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class MetricItemRead(MetricItemBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None