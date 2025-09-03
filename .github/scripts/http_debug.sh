#!/usr/bin/env bash
set -euo pipefail

# Minimal, consistent HTTP debug helpers for CI logs.
# Policy: Only obfuscate bearer tokens. Do not obfuscate URLs, application keys, payloads,
# or headers other than the Authorization token. Respect HTTP_DEBUG_LEVEL: none|basic|verbose.

# Prints a one-line curl that can be copy/pasted. The token is replaced with a placeholder.
# Usage: emit_curl_copy METHOD URL TOKEN JSON_BODY
emit_curl_copy() {
  local method="${1:-GET}"; shift || true
  local url="${1:-}"; shift || true
  local token="${1:-}"; shift || true
  local body="${1:-}"; shift || true
  local ct_header="-H 'Content-Type: application/json'";
  local accept_header="-H 'Accept: application/json'";
  local sanitized_body
  sanitized_body=$(printf "%s" "${body}" | jq -c 2>/dev/null || printf "%s" "${body}")
  echo "curl -X ${method} \"${url}\" -H 'Authorization: Bearer <REPLACE_WITH_ACCESS_TOKEN>' ${ct_header} ${accept_header} --data-raw '${sanitized_body}'"
}

# Print a structured debug block for an HTTP request. Only masks the token.
# Usage: print_request_debug METHOD URL [BODY]
print_request_debug() {
  local method="${1:-}"; local url="${2:-}"; local body="${3:-}"; local level="${HTTP_DEBUG_LEVEL:-basic}"
  [ "${level}" = "none" ] && return 0
  local show_project_header=false
  local show_content_type=false
  if [[ "${url}" == *"/apptrust/api/"* ]]; then
    if [[ "${url}" == *"/promote"* || "${url}" == *"/release"* ]]; then
      show_project_header=false
    else
      show_project_header=true
    fi
  fi
  if [[ "${method}" == "POST" ]]; then show_content_type=true; fi
  echo "---- Request debug (${level}) ----"
  echo "Method: ${method}"
  echo "URL: ${url}"
  echo "Headers:"
  echo "  Authorization: Bearer ***REDACTED***"
  if ${show_project_header} && [[ -n "${PROJECT_KEY:-}" ]]; then echo "  X-JFrog-Project: ${PROJECT_KEY}"; fi
  if ${show_content_type}; then echo "  Content-Type: application/json"; fi
  echo "  Accept: application/json"
  if [[ -n "${body}" && "${level}" = "verbose" ]]; then
    echo "Body: ${body}"
  fi
  echo "-----------------------"
}


