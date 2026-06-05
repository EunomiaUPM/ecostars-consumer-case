from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field


class Chain(SQLModel, table=True):
    __tablename__ = "chains"

    uuid: UUID = Field(primary_key=True)
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
