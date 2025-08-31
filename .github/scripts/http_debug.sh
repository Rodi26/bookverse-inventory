#!/usr/bin/env bash

print_request_debug() {
  local method="$1"; local url="$2"; local body="${3:-}"
  local level="${HTTP_DEBUG_LEVEL:-basic}"
  # Allow repo-level toggle: none|basic|verbose
  if [[ "$level" == "none" ]]; then return 0; fi
  echo "---- Request debug (${level}) ----"
  echo "Method: ${method}"
  echo "URL: ${url}"
  echo "Headers:"
  echo "  Authorization: Bearer ***REDACTED***"
  if [[ -n "${PROJECT_KEY:-}" ]]; then
    echo "  X-JFrog-Project: ${PROJECT_KEY}"
  fi
  echo "  Accept: application/json"
  if [[ "$level" == "verbose" ]]; then
    if [[ -n "$body" ]]; then
      echo "Body:"
      echo "$body"
    else
      echo "Body: (none)"
    fi
    echo "Reproduce locally with:"
    if [[ -n "$body" ]]; then
      echo "curl -v -X ${method} \"${url}\" \\\\" 
      echo "  -H \"Authorization: Bearer <TOKEN>\" \\\\" 
      echo "  -H \"X-JFrog-Project: ${PROJECT_KEY:-<PROJECT>}\" \\\\" 
      echo "  -H \"Accept: application/json\" \\\\" 
      echo "  -H \"Content-Type: application/json\" \\\\" 
      echo "  -d '$body'"
    else
      echo "curl -v -X ${method} \"${url}\" \\\\" 
      echo "  -H \"Authorization: Bearer <TOKEN>\" \\\\" 
      echo "  -H \"X-JFrog-Project: ${PROJECT_KEY:-<PROJECT>}\" \\\\" 
      echo "  -H \"Accept: application/json\""
    fi
  fi
  echo "-----------------------"
}


