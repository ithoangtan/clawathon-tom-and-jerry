#!/usr/bin/env bash
# Fail if AgentBase runtime env files contain forbidden keys.
# AgentBase rejects CLI-only / platform-injected vars in runtime configuration.
set -euo pipefail

FORBIDDEN_KEYS=(
  GREENNODE_CLIENT_ID
  GREENNODE_CLIENT_SECRET
  GREENNODE_AGENT_IDENTITY
  GREENNODE_ENDPOINT_URL
)

usage() {
  echo "Usage: $0 <env-file> [env-file ...]" >&2
  echo "Example: $0 .env" >&2
  exit 2
}

[[ $# -ge 1 ]] || usage

failures=0

check_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "ERROR: file not found: $file" >&2
    failures=$((failures + 1))
    return
  fi

  local line_num=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line_num=$((line_num + 1))
    # Strip leading whitespace; skip blanks and comments.
    local trimmed="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$trimmed" || "$trimmed" == \#* ]] && continue

    local key="${trimmed%%=*}"
    key="${key%"${key##*[![:space:]]}"}" # trim trailing space

    for forbidden in "${FORBIDDEN_KEYS[@]}"; do
      if [[ "$key" == "$forbidden" ]]; then
        echo "ERROR: $file:$line_num — forbidden runtime key: $forbidden" >&2
        echo "       Use deploy/operator-cli.env.example for CLI credentials (shell export only)." >&2
        failures=$((failures + 1))
      fi
    done
  done < "$file"
}

for file in "$@"; do
  check_file "$file"
done

if [[ "$failures" -gt 0 ]]; then
  echo "" >&2
  echo "Validation failed ($failures issue(s)). Forbidden runtime keys:" >&2
  printf '  - %s\n' "${FORBIDDEN_KEYS[@]}" >&2
  exit 1
fi

echo "OK: no forbidden runtime keys in ${#@} file(s)."
