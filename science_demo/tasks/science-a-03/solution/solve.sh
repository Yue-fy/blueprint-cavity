#!/bin/sh
set -eu
cat > "${1:-/workspace/answer.json}" <<'SCIENCE_ORACLE_JSON'
{
  "confidence": 1,
  "rationale": "Host-only offline reference oracle.",
  "value": 0.003925652940233937
}
SCIENCE_ORACLE_JSON
