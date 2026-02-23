from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class SubscriptionBase(SQLModel):
    url: Optional[str] = None
    event_type: Optional[str] = None

class Subscription(SubscriptionBase, table=True):
    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionRead(SubscriptionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None