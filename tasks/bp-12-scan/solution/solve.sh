#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 16, "unit": "in", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [2203.7752, 236.7507, 2381.0259, 261.2741], "space": "image_px", "note": "16\" SUCTION HEADER"}], "assumptions": ["Report nominal pipe size in inches, not the measured diameter of a line on the page."]}
BLUEPRINT_ORACLE_JSON
