#!/bin/bash

NIFI_REGISTRY_HOST="http://localhost:18080"
NIFI_REGISTRY_HOST_DOCKER="http://nifi-registry:18080"
NIFI_REGISTRY_API_URL="$NIFI_REGISTRY_HOST/nifi-registry-api"
NIFI_REGISTRY_NAME="ecostars"
NIFI_HOST="https://localhost:8443"
NIFI_API_URL="$NIFI_HOST/nifi-api"
NIFI_USER="nifi"
NIFI_PASS="nifinifinifinifi"

FLOW_DEFINITION_PATH=./flow_definitions/flow_definition.json
FLOW_DEFINITION_CONTENT=$(cat $FLOW_DEFINITION_PATH)

curl -k -X GET "$NIFI_API_URL/authentication/configuration"

# Authenticate and get access token
TOKEN=$(curl -k -X POST \
             -H 'Content-Type: application/x-www-form-urlencoded' \
             -d "username=$NIFI_USER&password=$NIFI_PASS" \
             "$NIFI_API_URL/access/token")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "Unauthorized" ]; then
    echo "Error: Not authenticated."
    exit 1
fi
AUTH_HEADER="Authorization: Bearer $TOKEN"


# Connect to NiFi Registry and create a new registry client
PAYLOAD='{
  "revision": {
    "version": 0
  },
  "component": {
    "name": "'"$NIFI_REGISTRY_NAME"'",
    "description": "Ecostars NiFi Registry",
    "type": "org.apache.nifi.registry.flow.NifiRegistryFlowRegistryClient", 
    "properties": {
      "url": "'"$NIFI_REGISTRY_HOST_DOCKER"'",
      "ssl-context-service": null
    }
  }
}'
curl -k -X POST \
     -H "$AUTH_HEADER" \
     -H 'Content-Type: application/json' \
     -d "$PAYLOAD" \
     "$NIFI_API_URL/controller/registry-clients"


# Fetch root process group ID
ROOT_PROCESS_GROUP_DETAILS=$(
  curl -k -X GET \
    -H "$AUTH_HEADER" \
    "$NIFI_API_URL/flow/process-groups/root"
)
CURRENT_ROOT_PROCESS_GROUP_ID=$(echo "$ROOT_PROCESS_GROUP_DETAILS" | jq -r '.processGroupFlow.id')
CURRENT_ROOT_PROCESS_GROUP_REVISION=$(echo "$ROOT_PROCESS_GROUP_DETAILS" | jq -r '.revision')
echo "Root Process group id: $CURRENT_ROOT_PROCESS_GROUP_ID"
echo "Current revision: $CURRENT_ROOT_PROCESS_GROUP_REVISION"

# Create new process group with the flow definition
FLOW_DEFINITION_SNAPSHOT='{
  "revision": '"$CURRENT_ROOT_PROCESS_GROUP_REVISION"',
  "component": {
    "name": "Ecostras Root Process Group",
    "position": { "x": 100, "y": 100 },
    "versionedFlowSnapshot": '"$FLOW_DEFINITION_CONTENT"' 
  }
}'

NEW_PROCESS_GROUP_RESPONSE=$(
  curl -k -X POST \
    -H "$AUTH_HEADER" \
    -H 'Content-Type: application/json' \
    -d "$FLOW_DEFINITION_SNAPSHOT" \
    "$NIFI_API_URL/process-groups/$CURRENT_ROOT_PROCESS_GROUP_ID/process-groups"
)
echo "New Process Group Response: $NEW_PROCESS_GROUP_RESPONSE"
NEW_PROCESS_GROUP_ID=$(echo "$NEW_PROCESS_GROUP_RESPONSE" | jq -r '.id')
echo "New Process Group ID: $NEW_PROCESS_GROUP_ID"