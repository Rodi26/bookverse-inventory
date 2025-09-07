#!/usr/bin/env bash
set -euo pipefail

# Promote/Release helper library sourced by the promotion workflow.
#
# Flow overview (how release is triggered):
# - The workflow step "Release to PROD" (in .github/workflows/promote.yml)
#   sets ALLOW_RELEASE=true and calls advance_one_step.
# - advance_one_step() computes the next stage. If that next stage equals
#   FINAL_STAGE (PROD) AND ALLOW_RELEASE=true, it invokes release_version().
# - release_version() performs the AppTrust Release API call:
#     POST /apptrust/api/v1/applications/{application_key}/versions/{version}/release
#   with a JSON payload (promotion_type copy + included_repository_keys)
#   to move the application version to the global release stage (PROD).
# - For non-final stages, advance_one_step() calls promote_to_stage() instead.

# Minimal debug printer; controlled by HTTP_DEBUG_LEVEL: none|basic|verbose
print_request_debug() {
  local method="${1:-}"; local url="${2:-}"; local body="${3:-}"; local level="${HTTP_DEBUG_LEVEL:-basic}"
  [ "$level" = "none" ] && return 0
  local show_project_header=false
  local show_content_type=false
  # For AppTrust APIs, only include X-JFrog-Project when the endpoint expects
  # project scoping (e.g., versions listing). Release/Promote endpoints do not
  # require the project header and may reject it.
  if [[ "$url" == *"/apptrust/api/"* ]]; then
    if [[ "$url" == *"/promote"* || "$url" == *"/release"* ]]; then
      show_project_header=false
    else
      show_project_header=true
    fi
  fi
  # Show Content-Type only for POST bodies to reduce noise.
  if [[ "$method" == "POST" ]]; then show_content_type=true; fi
  echo "---- Request debug (${level}) ----"
  echo "Method: ${method}"
  echo "URL: ${url}"
  echo "Headers:"
  echo "  Authorization: Bearer ***REDACTED***"
  if $show_project_header && [[ -n "${PROJECT_KEY:-}" ]]; then echo "  X-JFrog-Project: ${PROJECT_KEY}"; fi
  if $show_content_type; then echo "  Content-Type: application/json"; fi
  echo "  Accept: application/json"
  if [ -n "$body" ] && [ "$level" = "verbose" ]; then
    echo "Body: ${body}"
  fi
  echo "-----------------------"
}

# Translate a display stage name (e.g., DEV) to the API stage identifier:
# - Non-PROD stages must be project-prefixed for API calls (bookverse-DEV, etc.)
# - PROD remains the global release stage (no prefix)
api_stage_for() {
  local s="${1:-}"
  if [[ "$s" == "PROD" ]]; then
    echo "PROD"
  elif [[ "$s" == "${PROJECT_KEY:-}-"* ]]; then
    echo "$s"
  else
    echo "${PROJECT_KEY:-}-$s"
  fi
}

# Translate an API stage identifier to a display name used internally:
# - bookverse-DEV → DEV, bookverse-STAGING → STAGING
# - PROD remains PROD
display_stage_for() {
  local s="${1:-}"
  if [[ "$s" == "PROD" || "$s" == "${PROJECT_KEY:-}-PROD" ]]; then
    echo "PROD"
  elif [[ "$s" == "${PROJECT_KEY:-}-"* ]]; then
    echo "${s#${PROJECT_KEY:-}-}"
  else
    echo "$s"
  fi
}

# Query the AppTrust Version Summary to determine current stage and release status.
# On success, exports CURRENT_STAGE and RELEASE_STATUS to the environment, with
# CURRENT_STAGE in API form (e.g., bookverse-STAGING, PROD). Callers should wrap
# it with display_stage_for when comparing against human readable names.
fetch_summary() {
  local body
  body=$(mktemp)
  local code
  code=$(curl -sS -L -o "$body" -w "%{http_code}" \
    "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content" \
    -H "Authorization: Bearer ${JFROG_ADMIN_TOKEN}" \
    -H "Accept: application/json" || echo 000)
  if [[ "$code" -ge 200 && "$code" -lt 300 ]]; then
    CURRENT_STAGE=$(jq -r '.current_stage // empty' "$body" 2>/dev/null || echo "")
    RELEASE_STATUS=$(jq -r '.release_status // empty' "$body" 2>/dev/null || echo "")
  else
    echo "❌ Failed to fetch version summary (HTTP $code)" >&2
    print_request_debug "GET" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content"
    cat "$body" || true
    rm -f "$body"
    return 1
  fi
  rm -f "$body"
  echo "CURRENT_STAGE=${CURRENT_STAGE:-}" >> "$GITHUB_ENV"
  echo "RELEASE_STATUS=${RELEASE_STATUS:-}" >> "$GITHUB_ENV"
  echo "🔎 Current stage: $(display_stage_for "${CURRENT_STAGE:-UNASSIGNED}") (release_status=${RELEASE_STATUS:-unknown})"
}

# Small helper to POST JSON to AppTrust endpoints, capturing HTTP status and body.
# NOTE: Callers are responsible for printing request context (via print_request_debug)
# upon errors and for interpreting success/failure semantics.
apptrust_post() {
  local path="${1:-}"; local data="${2:-}"; local out_file="${3:-}"
  local status
  status=$(curl -sS -L -o "$out_file" -w "%{http_code}" -X POST \
    "${JFROG_URL}${path}" \
    -H "Authorization: Bearer ${JFROG_ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$data")
  echo "$status"
}

# Call the AppTrust Promote API to move the version to a non-final stage
promote_to_stage() {
  local target_stage_display="${1:-}"
  local resp_body http_status
  resp_body=$(mktemp)
  local api_stage
  api_stage=$(api_stage_for "$target_stage_display")
  echo "🚀 Promoting to ${target_stage_display} via AppTrust"
  http_status=$(apptrust_post \
    "/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/promote?async=false" \
    "{\"target_stage\": \"${api_stage}\", \"promotion_type\": \"move\"}" \
    "$resp_body")
  echo "HTTP $http_status"; cat "$resp_body" || true; echo
  rm -f "$resp_body"
  if [[ "$http_status" -lt 200 || "$http_status" -ge 300 ]]; then
    echo "❌ Promotion to ${target_stage_display} failed (HTTP $http_status)" >&2
    print_request_debug "POST" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/promote?async=false" "{\"target_stage\": \"${api_stage}\", \"promotion_type\": \"move\"}"
    return 1
  fi
  PROMOTED_STAGES="${PROMOTED_STAGES:-}${PROMOTED_STAGES:+ }${target_stage_display}"
  echo "PROMOTED_STAGES=${PROMOTED_STAGES}" >> "$GITHUB_ENV"
  fetch_summary
}

# Call the AppTrust Release API to move the version to the final release stage (PROD)
# NOTE: This function is NOT called directly by the workflow. The workflow
#       sets ALLOW_RELEASE=true and calls advance_one_step(); only when the
#       computed next stage equals FINAL_STAGE (PROD) will advance_one_step()
#       invoke release_version(). See advance_one_step() below.
# Call the AppTrust Release API to move the version to the final release stage (PROD)
#
# Payload selection rules (included_repository_keys):
# - If RELEASE_INCLUDED_REPO_KEYS is provided (JSON array), it is used verbatim.
# - Otherwise, infer repository keys from APPLICATION_KEY and PROJECT_KEY.
#   These should point to release-local repositories attached to PROD.
release_version() {
  local resp_body http_status
  resp_body=$(mktemp)
  echo "🚀 Releasing to ${FINAL_STAGE} via AppTrust Release API"
  # Build included repositories list if provided or infer from APPLICATION_KEY and PROJECT_KEY
  local payload
  if [[ -n "${RELEASE_INCLUDED_REPO_KEYS:-}" ]]; then
    payload=$(printf '{"promotion_type":"move","included_repository_keys":%s}' "${RELEASE_INCLUDED_REPO_KEYS}")
  else
    # Derive service name from application key: bookverse-<service>
    local service_name
    service_name="${APPLICATION_KEY#${PROJECT_KEY}-}"
    local repo_docker repo_python
    # Use exact internal release repositories for final PROD release
    repo_docker="${PROJECT_KEY}-${service_name}-internal-docker-release-local"
    repo_python="${PROJECT_KEY}-${service_name}-internal-python-release-local"
    payload=$(printf '{"promotion_type":"move","included_repository_keys":["%s","%s"]}' "$repo_docker" "$repo_python")
  fi
  http_status=$(curl -sS -L -o "$resp_body" -w "%{http_code}" -X POST \
    "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" \
    -H "Authorization: Bearer ${JFROG_ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$payload")
  echo "HTTP $http_status"; cat "$resp_body" || true; echo
  if [[ "$http_status" -lt 200 || "$http_status" -ge 300 ]]; then
    echo "❌ Release to ${FINAL_STAGE} failed (HTTP $http_status)" >&2
    print_request_debug "POST" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" "{\"promotion_type\":\"move\"}"
    rm -f "$resp_body"
    return 1
  fi
  rm -f "$resp_body"
  DID_RELEASE=true
  echo "DID_RELEASE=${DID_RELEASE}" >> "$GITHUB_ENV"
  PROMOTED_STAGES="${PROMOTED_STAGES:-}${PROMOTED_STAGES:+ }${FINAL_STAGE}"
  echo "PROMOTED_STAGES=${PROMOTED_STAGES}" >> "$GITHUB_ENV"
  fetch_summary
}

emit_json() {
  local out_file="${1:-}"; shift
  local content="$*"
  printf "%b\n" "$content" > "$out_file"
}

evd_create() {
  local predicate_file="${1:-}"; local predicate_type="${2:-}"; local markdown_file="${3:-}"
  local md_args=()
  if [[ -n "$markdown_file" ]]; then md_args+=(--markdown "$markdown_file"); fi
  jf evd create-evidence \
    --predicate "$predicate_file" \
    "${md_args[@]}" \
    --predicate-type "$predicate_type" \
    --release-bundle "$APPLICATION_KEY" \
    --release-bundle-version "$APP_VERSION" \
    --project "${PROJECT_KEY}" \
    --provider-id github-actions \
    --key "${EVIDENCE_PRIVATE_KEY:-}" \
    --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
}

attach_evidence_qa() {
  local now_ts scan_id med coll pass
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  scan_id=$(cat /proc/sys/kernel/random/uuid)
  med=$((2 + RANDOM % 5))
  emit_json dast-qa.json "{\n    \"environment\": \"QA\",\n    \"scanId\": \"${scan_id}\",\n    \"status\": \"PASSED\",\n    \"findings\": { \"critical\": 0, \"high\": 0, \"medium\": ${med} },\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  printf "# dast-scan\n" > dast-scan.md
  evd_create dast-qa.json "https://invicti.com/evidence/dast/v3" dast-scan.md
  coll=$(cat /proc/sys/kernel/random/uuid)
  pass=$((100 + RANDOM % 31))
  emit_json postman-qa.json "{\n    \"environment\": \"QA\",\n    \"collectionId\": \"${coll}\",\n    \"status\": \"PASSED\",\n    \"assertionsPassed\": ${pass},\n    \"assertionsFailed\": 0,\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  printf "# api-tests\n" > api-tests.md
  evd_create postman-qa.json "https://postman.com/evidence/collection/v2.2" api-tests.md
}

attach_evidence_staging() {
  local now_ts med_iac low_iac pent tid
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  med_iac=$((1 + RANDOM % 3)); low_iac=$((8 + RANDOM % 7))
  # Disabled: staging gate evidence is attached explicitly in workflow to avoid duplicates
  :
  pent=$(cat /proc/sys/kernel/random/uuid)
  # Disabled duplicate pentest evidence; handled by workflow
  :
  tid=$((3000000 + RANDOM % 1000000))
  # Disabled duplicate ServiceNow approval; handled by workflow
  :
}

attach_evidence_prod() {
  local now_ts rev short
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  rev="${GITHUB_SHA:-${GITHUB_SHA:-}}"; short=${rev:0:8}
  emit_json argocd-prod.json "{ \"tool\": \"ArgoCD\", \"status\": \"Synced\", \"revision\": \"${short}\", \"deployedAt\": \"${now_ts}\", \"attachStage\": \"PROD\" }"
  printf "# argocd-deploy\n" > argocd-deploy.md
  # Use a shortened predicate-type to ensure type slug < 16 chars
  evd_create argocd-prod.json "https://argo.cd/ev/deploy/v1" argocd-deploy.md
}

attach_evidence_for() {
  local stage_name="${1:-}"
  case "$stage_name" in
    UNASSIGNED)
      echo "ℹ️ No evidence for UNASSIGNED" ;;
    DEV)
      echo "ℹ️ No evidence configured for DEV in demo" ;;
    QA)
      attach_evidence_qa ;;
    STAGING)
      attach_evidence_staging ;;
    PROD)
      attach_evidence_prod ;;
    *)
      echo "ℹ️ No evidence rule for stage '$stage_name'" ;;
  esac
}

# Compute the next stage and perform a single transition:
# - If next != FINAL_STAGE → promote_to_stage(next) + attach stage evidence
# - If next == FINAL_STAGE and ALLOW_RELEASE=true → release_version() + PROD evidence
# - If ALLOW_RELEASE=false, the release step is deferred to the dedicated
#   "Release to PROD" workflow step.
advance_one_step() {
  local allow_release="${ALLOW_RELEASE:-false}"
  # Build stages array from STAGES_STR
  IFS=' ' read -r -a STAGES <<< "${STAGES_STR:-}"
  local current_index=-1
  if [[ -z "${CURRENT_STAGE:-}" || "${CURRENT_STAGE}" == "UNASSIGNED" ]]; then
    current_index=-1
  else
    local i; for i in "${!STAGES[@]}"; do
      if [[ "$(api_stage_for "${STAGES[$i]}")" == "$(api_stage_for "${CURRENT_STAGE}")" ]]; then current_index=$i; break; fi
    done
  fi
  local target_index=-1
  local j; for j in "${!STAGES[@]}"; do if [[ "${STAGES[$j]}" == "${TARGET_NAME}" ]]; then target_index=$j; break; fi; done
  if [[ "$target_index" -lt 0 ]]; then echo "❌ Target stage '${TARGET_NAME}' not found in lifecycle. Available: ${STAGES[*]}" >&2; return 1; fi
  if [[ "$current_index" -ge "$target_index" ]]; then echo "ℹ️ Current stage (${CURRENT_STAGE:-UNASSIGNED}) is at or beyond target (${TARGET_NAME}). Nothing to promote."; return 0; fi
  local next_index=$((current_index+1))
  if [[ "$next_index" -gt "$target_index" ]]; then echo "ℹ️ Next stage would exceed target (${TARGET_NAME}). Nothing to promote."; return 0; fi
  local next_stage_display="${STAGES[$next_index]}"
  if [[ "$next_stage_display" == "$FINAL_STAGE" ]]; then
    if [[ "$allow_release" == "true" ]]; then
      release_version || return 1
      attach_evidence_prod || true
    else
      echo "⏭️ Skipping release step (deferred to dedicated step)"
    fi
  else
    promote_to_stage "$next_stage_display" || return 1
    attach_evidence_for "$next_stage_display" || true
  fi
}


