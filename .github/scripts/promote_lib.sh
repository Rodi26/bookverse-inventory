#!/usr/bin/env bash
set -euo pipefail

# Minimal debug printer; controlled by HTTP_DEBUG_LEVEL: none|basic|verbose
print_request_debug() {
  local method="${1:-}"; local url="${2:-}"; local body="${3:-}"; local level="${HTTP_DEBUG_LEVEL:-basic}"
  [ "$level" = "none" ] && return 0
  local show_project_header=false
  local show_content_type=false
  if [[ "$url" == *"/apptrust/api/"* ]]; then
    if [[ "$url" == *"/promote"* || "$url" == *"/release"* ]]; then
      show_project_header=false
    else
      show_project_header=true
    fi
  fi
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

fetch_summary() {
  local body
  body=$(mktemp)
  local code
  code=$(curl -sS -L -o "$body" -w "%{http_code}" \
    "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/content" \
    -H "Authorization: Bearer ${JFROG_ADMIN_TOKEN}" \
    -H "X-JFrog-Project: ${PROJECT_KEY}" \
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

release_version() {
  local resp_body http_status
  resp_body=$(mktemp)
  echo "🚀 Releasing to ${FINAL_STAGE} via AppTrust Release API"
  http_status=$(apptrust_post \
    "/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" \
    "{\"promotion_type\":\"move\"}" \
    "$resp_body")
  echo "HTTP $http_status"; cat "$resp_body" || true; echo
  rm -f "$resp_body"
  if [[ "$http_status" -lt 200 || "$http_status" -ge 300 ]]; then
    echo "❌ Release to ${FINAL_STAGE} failed (HTTP $http_status)" >&2
    print_request_debug "POST" "${JFROG_URL}/apptrust/api/v1/applications/${APPLICATION_KEY}/versions/${APP_VERSION}/release?async=false" "{\"promotion_type\":\"move\"}"
    return 1
  fi
  DID_RELEASE=true
  echo "DID_RELEASE=${DID_RELEASE}" >> "$GITHUB_ENV"
  PROMOTED_STAGES="${PROMOTED_STAGES:-}${PROMOTED_STAGES:+ }${FINAL_STAGE}"
  echo "PROMOTED_STAGES=${PROMOTED_STAGES}" >> "$GITHUB_ENV"
  fetch_summary
}

emit_json() {
  local out_file="${1:-}"; shift
  local content="$*"
  printf "%s\n" "$content" > "$out_file"
}

evd_create() {
  local predicate_file="${1:-}"; local predicate_type="${2:-}"
  local key_args=()
  if [[ -n "${EVIDENCE_PRIVATE_KEY:-}" ]]; then key_args+=(--key "${EVIDENCE_PRIVATE_KEY}"); fi
  jf evd create-evidence \
    --predicate "$predicate_file" \
    --predicate-type "$predicate_type" \
    --release-bundle "$APPLICATION_KEY" \
    --release-bundle-version "$APP_VERSION" \
    --project "${PROJECT_KEY}" \
    --provider-id github-actions \
    "${key_args[@]}" || true
}

attach_evidence_qa() {
  local now_ts scan_id med coll pass
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  scan_id=$(cat /proc/sys/kernel/random/uuid)
  med=$((2 + RANDOM % 5))
  emit_json dast-qa.json "{\n    \"environment\": \"QA\",\n    \"scanId\": \"${scan_id}\",\n    \"status\": \"PASSED\",\n    \"findings\": { \"critical\": 0, \"high\": 0, \"medium\": ${med} },\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  evd_create dast-qa.json "https://invicti.com/evidence/dast/v3"
  coll=$(cat /proc/sys/kernel/random/uuid)
  pass=$((100 + RANDOM % 31))
  emit_json postman-qa.json "{\n    \"environment\": \"QA\",\n    \"collectionId\": \"${coll}\",\n    \"status\": \"PASSED\",\n    \"assertionsPassed\": ${pass},\n    \"assertionsFailed\": 0,\n    \"attachStage\": \"QA\", \"gateForPromotionTo\": \"STAGING\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  evd_create postman-qa.json "https://postman.com/evidence/collection/v2.2"
}

attach_evidence_staging() {
  local now_ts med_iac low_iac pent tid
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  med_iac=$((1 + RANDOM % 3)); low_iac=$((8 + RANDOM % 7))
  emit_json iac-staging.json "{\n    \"environment\": \"STAGING\", \"status\": \"PASSED\",\n    \"misconfigurations\": { \"high\": 0, \"medium\": ${med_iac}, \"low\": ${low_iac} },\n    \"attachStage\": \"STAGING\", \"gateForPromotionTo\": \"PROD\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  evd_create iac-staging.json "https://snyk.io/evidence/iac/v1"
  pent=$(cat /proc/sys/kernel/random/uuid)
  emit_json pentest-staging.json "{\n    \"environment\": \"STAGING\", \"pentestId\": \"${pent}\",\n    \"status\": \"COMPLETED\", \"summary\": \"No critical/high. Medium/low scheduled for remediation.\",\n    \"attachStage\": \"STAGING\", \"gateForPromotionTo\": \"PROD\",\n    \"timestamp\": \"${now_ts}\"\n  }"
  evd_create pentest-staging.json "https://cobalt.io/evidence/pentest/v1"
  tid=$((3000000 + RANDOM % 1000000))
  emit_json servicenow-approval.json "{\n    \"environment\": \"PROD\",\n    \"ticketId\": \"CHG${tid}\",\n    \"status\": \"APPROVED\",\n    \"approvedBy\": \"change-manager-${RANDOM}\",\n    \"approvalTimestamp\": \"${now_ts}\",\n    \"attachStage\": \"STAGING\", \"gateForPromotionTo\": \"PROD\"\n  }"
  evd_create servicenow-approval.json "https://servicenow.com/evidence/change-request/v1"
}

attach_evidence_prod() {
  local now_ts rev short
  now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  rev="${GITHUB_SHA:-${GITHUB_SHA:-}}"; short=${rev:0:8}
  emit_json argocd-prod.json "{ \"tool\": \"ArgoCD\", \"status\": \"Synced\", \"revision\": \"${short}\", \"deployedAt\": \"${now_ts}\", \"attachStage\": \"PROD\" }"
  evd_create argocd-prod.json "https://argoproj.github.io/argo-cd/evidence/deployment/v1"
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


