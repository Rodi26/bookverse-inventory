#!/bin/bash
set -euo pipefail

# Manual promotion test script
# Tests direct API calls to promote an existing application version

echo "🧪 Manual Promotion Test Script"
echo "================================"

# Configuration
JFROG_URL="https://apptrustswampupc.jfrog.io"
PROJECT_KEY="bookverse"
APPLICATION_KEY="bookverse-inventory"
APP_VERSION="${1:-5.32.90}"  # Use provided version or default
PROVIDER_NAME="bookverse-inventory-github"

echo "📋 Configuration:"
echo "  JFrog URL: $JFROG_URL"
echo "  Project: $PROJECT_KEY"
echo "  Application: $APPLICATION_KEY"
echo "  Version: $APP_VERSION"
echo ""

# Step 1: Get OIDC token
echo "🔐 Step 1: Getting OIDC token..."
if [[ -z "${ACTIONS_ID_TOKEN_REQUEST_URL:-}" || -z "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:-}" ]]; then
  echo "❌ This script must run in GitHub Actions environment"
  echo "   Missing ACTIONS_ID_TOKEN_REQUEST_URL or ACTIONS_ID_TOKEN_REQUEST_TOKEN"
  exit 1
fi

GH_ID_TOKEN=$(curl -sS -H "Authorization: Bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
  "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=${JFROG_URL}" | jq -r .value)

if [[ -z "$GH_ID_TOKEN" || "$GH_ID_TOKEN" == "null" ]]; then
  echo "❌ Failed to get GitHub ID token"
  exit 1
fi

echo "✅ GitHub ID token obtained"

# Step 2: Exchange for JFrog access token
echo "🔄 Step 2: Exchanging for JFrog access token..."
PAYLOAD=$(jq -n --arg jwt "$GH_ID_TOKEN" \
  '{grant_type: "urn:ietf:params:oauth:grant-type:token-exchange", subject_token: $jwt, subject_token_type: "urn:ietf:params:oauth:token-type:id_token", provider_name: env.PROVIDER_NAME}')

JF_ACCESS_TOKEN=$(curl -sS -X POST "${JFROG_URL}/access/api/v1/oidc/token" \
  -H "Content-Type: application/json" -d "$PAYLOAD" | jq -r .access_token)

if [[ -z "$JF_ACCESS_TOKEN" || "$JF_ACCESS_TOKEN" == "null" ]]; then
  echo "❌ Failed to exchange for JFrog access token"
  exit 1
fi

echo "✅ JFrog access token obtained"

# Step 3: Check current application version status
echo "📊 Step 3: Checking current application version status..."
CONTENT_RESP=$(mktemp)
CONTENT_STATUS=$(curl -sS -L -o "$CONTENT_RESP" -w "%{http_code}" \
  "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content" \
  -H "Authorization: Bearer $JF_ACCESS_TOKEN" \
  -H "Accept: application/json")

if [[ "$CONTENT_STATUS" != "200" ]]; then
  echo "❌ Failed to get application version content (HTTP $CONTENT_STATUS)"
  echo "Response:"
  cat "$CONTENT_RESP" || true
  rm -f "$CONTENT_RESP"
  exit 1
fi

echo "✅ Application version found"
echo "📄 Current status:"
cat "$CONTENT_RESP" | jq .
echo ""

CURRENT_STAGE=$(jq -r '.current_stage // empty' "$CONTENT_RESP")
RELEASE_STATUS=$(jq -r '.release_status // empty' "$CONTENT_RESP")
VERSION_STATUS=$(jq -r '.status // empty' "$CONTENT_RESP")

echo "🏷️ Current stage: '${CURRENT_STAGE:-UNASSIGNED}'"
echo "🏷️ Release status: '${RELEASE_STATUS:-unknown}'"
echo "🏷️ Version status: '${VERSION_STATUS:-unknown}'"
echo ""

rm -f "$CONTENT_RESP"

# Step 4: Test promotion to DEV
echo "🚀 Step 4: Testing promotion to DEV..."
TARGET_STAGE="bookverse-DEV"
PROMOTE_PAYLOAD=$(jq -nc --arg to "$TARGET_STAGE" '{to_stage:$to}')

echo "📋 Promotion payload:"
echo "$PROMOTE_PAYLOAD" | jq .

PROMOTE_RESP=$(mktemp)
PROMOTE_STATUS=$(curl -sS -L -o "$PROMOTE_RESP" -w "%{http_code}" -X POST \
  "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/promote" \
  -H "Authorization: Bearer $JF_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "$PROMOTE_PAYLOAD")

echo "🔢 Promotion HTTP Status: $PROMOTE_STATUS"
echo "📨 Promotion Response:"
cat "$PROMOTE_RESP" | jq . 2>/dev/null || cat "$PROMOTE_RESP"
echo ""

if [[ "$PROMOTE_STATUS" -ge 200 && "$PROMOTE_STATUS" -lt 300 ]]; then
  echo "✅ Promotion API call succeeded"
else
  echo "❌ Promotion API call failed"
  rm -f "$PROMOTE_RESP"
  exit 1
fi

rm -f "$PROMOTE_RESP"

# Step 5: Check if stage actually changed
echo "🔍 Step 5: Verifying stage change..."
sleep 2  # Brief pause for any async processing

VERIFY_RESP=$(mktemp)
VERIFY_STATUS=$(curl -sS -L -o "$VERIFY_RESP" -w "%{http_code}" \
  "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content" \
  -H "Authorization: Bearer $JF_ACCESS_TOKEN" \
  -H "Accept: application/json")

if [[ "$VERIFY_STATUS" != "200" ]]; then
  echo "❌ Failed to verify stage change (HTTP $VERIFY_STATUS)"
  rm -f "$VERIFY_RESP"
  exit 1
fi

NEW_STAGE=$(jq -r '.current_stage // empty' "$VERIFY_RESP")
NEW_RELEASE_STATUS=$(jq -r '.release_status // empty' "$VERIFY_RESP")

echo "📄 Updated status:"
cat "$VERIFY_RESP" | jq .
echo ""

echo "🏷️ New stage: '${NEW_STAGE:-UNASSIGNED}'"
echo "🏷️ New release status: '${NEW_RELEASE_STATUS:-unknown}'"

rm -f "$VERIFY_RESP"

# Final result
if [[ "$NEW_STAGE" != "$CURRENT_STAGE" ]]; then
  echo "🎉 SUCCESS: Stage changed from '${CURRENT_STAGE:-UNASSIGNED}' to '${NEW_STAGE:-UNASSIGNED}'"
else
  echo "❌ FAILURE: Stage did not change (still '${CURRENT_STAGE:-UNASSIGNED}')"
  echo "   This indicates the promotion API call succeeded but didn't actually promote"
  exit 1
fi
