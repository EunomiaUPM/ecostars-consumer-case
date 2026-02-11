#!/bin/sh

NIFI_REGISTRY_HOST="http://${NIFI_REGISTRY_SERVICE}:18080"
NIFI_REGISTRY_API_URL="$NIFI_REGISTRY_HOST/nifi-registry-api"
NIFI_REGISTRY_NAME="ecostars"
NIFI_HOST="https://${NIFI_SERVICE}:8443"
NIFI_API_URL="$NIFI_HOST/nifi-api"
NIFI_USER="nifi"
NIFI_PASS="nifinifinifinifi"

FLOW_DEFINITION_PATH=/data/flow_definition.json

echo "Checking NiFi authentication configuration..."
curl -k -s "$NIFI_API_URL/authentication/configuration"
echo ""

# Authenticate and get access token
echo "Authenticating with NiFi..."
TOKEN=$(curl -k -s -X POST \
             -H 'Content-Type: application/x-www-form-urlencoded' \
             -d "username=$NIFI_USER&password=$NIFI_PASS" \
             "$NIFI_API_URL/access/token")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "Unauthorized" ]; then
    echo "Error: Not authenticated."
    exit 1
fi
AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "Authenticated successfully."

# Connect to NiFi Registry and create a new registry client
echo "Registering NiFi Registry client..."
cat > /tmp/registry_payload.json <<EOF
{
  "revision": {
    "version": 0
  },
  "component": {
    "name": "$NIFI_REGISTRY_NAME",
    "description": "Ecostars NiFi Registry",
    "type": "org.apache.nifi.registry.flow.NifiRegistryFlowRegistryClient",
    "properties": {
      "url": "$NIFI_REGISTRY_HOST",
      "ssl-context-service": null
    }
  }
}
EOF
curl -k -s -X POST \
     -H "$AUTH_HEADER" \
     -H 'Content-Type: application/json' \
     -d @/tmp/registry_payload.json \
     "$NIFI_API_URL/controller/registry-clients"
echo ""

# Fetch root process group ID
echo "Fetching root process group..."
ROOT_PG_RESPONSE=$(curl -k -s -X GET \
    -H "$AUTH_HEADER" \
    "$NIFI_API_URL/flow/process-groups/root")

CURRENT_ROOT_PG_ID=$(echo "$ROOT_PG_RESPONSE" | jq -r '.processGroupFlow.id')
CURRENT_REVISION=$(echo "$ROOT_PG_RESPONSE" | jq -c '.revision')
echo "Root Process group id: $CURRENT_ROOT_PG_ID"
echo "Current revision: $CURRENT_REVISION"

# Build the flow definition payload using jq (avoids "Argument list too long")
echo "Building flow definition payload..."
jq -n \
  --argjson revision "$CURRENT_REVISION" \
  --slurpfile flow "$FLOW_DEFINITION_PATH" \
  '{
    revision: $revision,
    component: {
      name: "Ecostars Root Process Group",
      position: { x: 100, y: 100 },
      versionedFlowSnapshot: $flow[0]
    }
  }' > /tmp/flow_payload.json

# Import the flow definition from file
echo "Importing flow definition..."
NEW_PG_RESPONSE=$(curl -k -s -X POST \
    -H "$AUTH_HEADER" \
    -H 'Content-Type: application/json' \
    -d @/tmp/flow_payload.json \
    "$NIFI_API_URL/process-groups/$CURRENT_ROOT_PG_ID/process-groups")

NEW_PG_ID=$(echo "$NEW_PG_RESPONSE" | jq -r '.id')
echo "New Process Group ID: $NEW_PG_ID"

echo "NiFi setup completed successfully."