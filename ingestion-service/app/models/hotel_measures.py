from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class HotelMeasureBase(SQLModel):
    hotel_id: Optional[int] = Field(default=None, foreign_key="hotels.id")
    year: Optional[int] = None
    rooms: Optional[int] = None
    stays: Optional[int] = None
    gas_kwh: Optional[float] = None
    water_m3: Optional[float] = None
    occupied: Optional[int] = None
    deviation: Optional[float] = None
    energy_kwh: Optional[float] = None
    rating_co2: Optional[float] = None
    total_area: Optional[float] = None
    stays_per_rn: Optional[float] = None
    electricity: Optional[float] = None
    rating_co2_rn: Optional[float] = None
    rating_water: Optional[float] = None
    deviation_co2: Optional[float] = None
    rating_energy: Optional[float] = None
    rating_co2_s1_rn: Optional[float] = None
    rating_co2_s2_rn: Optional[float] = None
    rating_co2_stay: Optional[float] = None
    rating_water_rn: Optional[float] = None
    deviation_co2_rn: Optional[float] = None
    deviation_waste: Optional[float] = None
    deviation_water: Optional[float] = None
    electricity_kwh: Optional[float] = None
    rating_energy_rn: Optional[float] = None
    total_emissions: Optional[float] = None
    co2_compensation: Optional[float] = None
    deviation_energy: Optional[float] = None
    rating_co2_s1_stay: Optional[float] = None
    rating_co2_s2_stay: Optional[float] = None
    rating_water_area: Optional[float] = None
    rating_water_room: Optional[float] = None
    rating_water_stay: Optional[float] = None
    scope1_emissions: Optional[float] = None
    scope2_emissions: Optional[float] = None
    deviation_co2_s1_rn: Optional[float] = None
    deviation_co2_s2_rn: Optional[float] = None
    deviation_co2_s3_rn: Optional[float] = None
    deviation_co2_stay: Optional[float] = None
    deviation_waste_rn: Optional[float] = None
    deviation_water_rn: Optional[float] = None
    direct_stationary: Optional[float] = None
    rating_energy_area: Optional[float] = None
    rating_energy_room: Optional[float] = None
    rating_energy_stay: Optional[float] = None
    recommended_stars: Optional[float] = None
    deviation_energy_rn: Optional[float] = None
    deviation_co2_s1_stay: Optional[float] = None
    deviation_co2_s2_stay: Optional[float] = None
    deviation_co2_s3_stay: Optional[float] = None
    deviation_waste_stay: Optional[float] = None
    deviation_water_stay: Optional[float] = None
    recommended_stars_v1: Optional[float] = None
    recommended_stars_v2: Optional[float] = None
    scope2_compensation: Optional[float] = None
    deviation_energy_stay: Optional[float] = None
    energy_kwh_with_co2_compensation: Optional[float] = None
    rating_energy_with_co2_compensation: Optional[float] = None
    deviation_energy_with_co2_compensation: Optional[float] = None

class HotelMeasure(HotelMeasureBase, table=True):
    __tablename__ = "hotel_measures"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class HotelMeasureCreate(HotelMeasureBase):
    pass

class HotelMeasureRead(HotelMeasureBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None