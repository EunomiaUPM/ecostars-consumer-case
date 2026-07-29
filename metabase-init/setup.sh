#!/bin/sh
# Completes the Metabase setup wizard unattended: creates the admin user and
# registers transactional-db as a data source.
#
# The open source edition cannot provision users from environment variables or
# a config file (that is a Pro/Enterprise feature), so the only supported way
# is POST /api/setup. We deliberately do not use MB_SETUP_TOKEN: passing a
# fixed token leaves the frontend stuck in setup mode (metabase#12874).
# Instead we read the token Metabase generates at boot, which also makes this
# script idempotent - once setup is done the token is gone.
set -eu

MB_URL="${MB_URL:-http://metabase:3000}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180}"

log() { echo "[metabase-setup] $*"; }

die() {
    log "ERROR: $1"
    [ -n "${2:-}" ] && { head -c 800 "$2"; echo; }
    exit 1
}

log "waiting for ${MB_URL} to become healthy (timeout ${WAIT_TIMEOUT}s)"
elapsed=0
while [ "$elapsed" -lt "$WAIT_TIMEOUT" ]; do
    curl -sf -o /dev/null "${MB_URL}/api/health" && break
    sleep 3
    elapsed=$((elapsed + 3))
done
[ "$elapsed" -lt "$WAIT_TIMEOUT" ] || die "Metabase did not become healthy in ${WAIT_TIMEOUT}s"
log "Metabase is up"

# --- Admin user ------------------------------------------------------------
TOKEN=$(curl -sf "${MB_URL}/api/session/properties" | jq -r '."setup-token" // empty')
if [ -n "$TOKEN" ]; then
    log "running setup for ${MB_ADMIN_EMAIL}"
    BODY=$(jq -n \
        --arg token "$TOKEN" \
        --arg email "$MB_ADMIN_EMAIL" \
        --arg pass "$MB_ADMIN_PASSWORD" \
        --arg first "$MB_ADMIN_FIRST_NAME" \
        --arg last "$MB_ADMIN_LAST_NAME" \
        --arg site "$MB_SITE_NAME" \
        '{
            token: $token,
            user: {
                first_name: $first, last_name: $last,
                email: $email, password: $pass, site_name: $site
            },
            prefs: { site_name: $site, allow_tracking: false }
        }')
    OUT=$(mktemp)
    CODE=$(curl -s -o "$OUT" -w '%{http_code}' -X POST "${MB_URL}/api/setup" \
        -H 'Content-Type: application/json' -d "$BODY")
    case "$CODE" in
        2*) log "admin user created" ;;
        *)  die "POST /api/setup returned HTTP ${CODE}" "$OUT" ;;
    esac
else
    log "admin user already exists"
fi

# --- Data source -----------------------------------------------------------
# Added separately on purpose: /api/setup accepts a "database" key but silently
# ignores it, leaving only the bundled Sample Database behind.
SESSION=$(curl -sf -X POST "${MB_URL}/api/session" -H 'Content-Type: application/json' \
    -d "$(jq -n --arg u "$MB_ADMIN_EMAIL" --arg p "$MB_ADMIN_PASSWORD" \
        '{username:$u, password:$p}')" | jq -r '.id // empty')
[ -n "$SESSION" ] || die "could not log in as ${MB_ADMIN_EMAIL}"

EXISTING=$(curl -sf -H "X-Metabase-Session: ${SESSION}" "${MB_URL}/api/database" \
    | jq -r --arg n "$MB_SOURCE_DB_NAME" '[(.data // .)[]? | select(.name == $n)] | length')
if [ "$EXISTING" != "0" ]; then
    log "data source '${MB_SOURCE_DB_NAME}' already registered"
    exit 0
fi

log "registering data source '${MB_SOURCE_DB_NAME}'"
BODY=$(jq -n \
    --arg name "$MB_SOURCE_DB_NAME" \
    --arg host "$MB_SOURCE_DB_HOST" \
    --argjson port "$MB_SOURCE_DB_PORT" \
    --arg dbname "$MB_SOURCE_DB_DATABASE" \
    --arg user "$MB_SOURCE_DB_USER" \
    --arg pass "$MB_SOURCE_DB_PASSWORD" \
    '{
        engine: "postgres",
        name: $name,
        details: {
            host: $host, port: $port, dbname: $dbname,
            user: $user, password: $pass, ssl: false
        }
    }')
OUT=$(mktemp)
CODE=$(curl -s -o "$OUT" -w '%{http_code}' -X POST "${MB_URL}/api/database" \
    -H "X-Metabase-Session: ${SESSION}" -H 'Content-Type: application/json' -d "$BODY")
case "$CODE" in
    2*) log "setup complete - admin is ${MB_ADMIN_EMAIL}, data source '${MB_SOURCE_DB_NAME}' added" ;;
    *)  die "POST /api/database returned HTTP ${CODE}" "$OUT" ;;
esac
