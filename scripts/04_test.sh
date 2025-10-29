#!/bin/bash

PUSH_URL=http://127.0.0.1:9090/consumer-data/push
PUSH_TEST_DATA='{
  "id": 1,
  "item_type": "hotel_occupancy",
  "last_value": 75.5,
  "last_measured_at": "2025-10-28T00:00:00Z"
}'

curl -i -X POST $PUSH_URL -H "Content-Type: application/json" -d $PUSH_TEST_DATA