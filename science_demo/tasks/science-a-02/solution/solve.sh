#!/bin/sh
set -eu
cat > "${1:-/workspace/answer.json}" <<'SCIENCE_ORACLE_JSON'
{
  "confidence": 1,
  "rationale": "Host-only offline reference oracle.",
  "value": 0.00554016620498615
}
SCIENCE_ORACLE_JSON
