#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 16, "unit": "in", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [1317.1, 141.461, 1423.035, 156.114], "space": "pdf_pt", "note": "16\" SUCTION HEADER"}], "assumptions": ["Report nominal pipe size in inches, not the measured diameter of a line on the page."]}
BLUEPRINT_ORACLE_JSON
