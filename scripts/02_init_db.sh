#!/bin/bash

DROP_TABLE_STATEMENT="DROP TABLE IF EXISTS metrics;"
CREATE_PUSH_TABLE_STATEMENT="CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_id VARCHAR(100) NOT NULL,
    item_type VARCHAR(100) NOT NULL,
    last_value VARCHAR(100) NOT NULL,
    last_measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

DROP_PULL_HOTEL_TABLE_STATEMENT="DROP TABLE IF EXISTS hotel;"
CREATE_PULL_HOTEL_TABLE_STATEMENT="CREATE TABLE IF NOT EXISTS hotel (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL
);"

DROP_PULL_HOTEL_MEASURE_TABLE_STATEMENT="DROP TABLE IF EXISTS hotel_measure;"
CREATE_PULL_HOTEL_MEASURE_TABLE_STATEMENT="CREATE TABLE IF NOT EXISTS hotel_measure (
    "id" BIGINT PRIMARY KEY,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "deleted_at" TIMESTAMP,
    "hotel_id" BIGINT NOT NULL,
    "year" INTEGER,
    "rooms" INTEGER,
    "stays" BIGINT,
    "gas_kwh" DOUBLE PRECISION,
    "water_m3" DOUBLE PRECISION,
    "occupied" BIGINT,
    "deviation" DOUBLE PRECISION,
    "energy_kwh" DOUBLE PRECISION,
    "rating_co2" DOUBLE PRECISION,
    "total_area" DOUBLE PRECISION,
    "stays_per_rn" DOUBLE PRECISION,
    "electricity" DOUBLE PRECISION,
    "rating_co2_rn" DOUBLE PRECISION,
    "rating_water" DOUBLE PRECISION,
    "deviation_co2" DOUBLE PRECISION,
    "rating_energy" DOUBLE PRECISION,
    "rating_co2_s1_rn" DOUBLE PRECISION,
    "rating_co2_s2_rn" DOUBLE PRECISION,
    "rating_co2_stay" DOUBLE PRECISION,
    "rating_water_rn" DOUBLE PRECISION,
    "deviation_co2_rn" DOUBLE PRECISION,
    "deviation_waste" DOUBLE PRECISION,
    "deviation_water" DOUBLE PRECISION,
    "electricity_kwh" DOUBLE PRECISION,
    "rating_energy_rn" DOUBLE PRECISION,
    "total_emissions" DOUBLE PRECISION,
    "co2_compensation" DOUBLE PRECISION,
    "deviation_energy" DOUBLE PRECISION,
    "rating_co2_s1_stay" DOUBLE PRECISION,
    "rating_co2_s2_stay" DOUBLE PRECISION,
    "rating_water_area" DOUBLE PRECISION,
    "rating_water_room" DOUBLE PRECISION,
    "rating_water_stay" DOUBLE PRECISION,
    "scope1_emissions" DOUBLE PRECISION,
    "scope2_emissions" DOUBLE PRECISION,
    "deviation_co2_s1_rn" DOUBLE PRECISION,
    "deviation_co2_s2_rn" DOUBLE PRECISION,
    "deviation_co2_s3_rn" DOUBLE PRECISION,
    "deviation_co2_stay" DOUBLE PRECISION,
    "deviation_waste_rn" DOUBLE PRECISION,
    "deviation_water_rn" DOUBLE PRECISION,
    "direct_stationary" DOUBLE PRECISION,
    "rating_energy_area" DOUBLE PRECISION,
    "rating_energy_room" DOUBLE PRECISION,
    "rating_energy_stay" DOUBLE PRECISION,
    "recommended_stars" DOUBLE PRECISION,
    "deviation_energy_rn" DOUBLE PRECISION,
    "deviation_co2_s1_stay" DOUBLE PRECISION,
    "deviation_co2_s2_stay" DOUBLE PRECISION,
    "deviation_co2_s3_stay" DOUBLE PRECISION,
    "deviation_waste_stay" DOUBLE PRECISION,
    "deviation_water_stay" DOUBLE PRECISION,
    "recommended_stars_v1" DOUBLE PRECISION,
    "recommended_stars_v2" DOUBLE PRECISION,
    "scope2_compensation" DOUBLE PRECISION,
    "deviation_energy_stay" DOUBLE PRECISION,
    "energy_kwh_with_co2_compensation" DOUBLE PRECISION,
    "rating_energy_with_co2_compensation" DOUBLE PRECISION,
    "deviation_energy_with_co2_compensation" DOUBLE PRECISION,

    CONSTRAINT fk_hotel
      FOREIGN KEY("hotel_id") 
      REFERENCES hotel(id)
      ON DELETE CASCADE
);"

POSTGRES_USER=postgres
POSTGRES_DB=postgres
TRANSACTIONAL_CONTAINER=transactional-db
docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$DROP_TABLE_STATEMENT"
docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$DROP_PULL_HOTEL_MEASURE_TABLE_STATEMENT"
docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$DROP_PULL_HOTEL_TABLE_STATEMENT"


docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$CREATE_PUSH_TABLE_STATEMENT"
docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$CREATE_PULL_HOTEL_TABLE_STATEMENT"
docker exec -i "$TRANSACTIONAL_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$CREATE_PULL_HOTEL_MEASURE_TABLE_STATEMENT"