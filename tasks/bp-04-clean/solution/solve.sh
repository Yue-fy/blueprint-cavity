#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 9.96, "unit": "m", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [2046.0055, 2282.5733, 2164.9452, 2352.4808], "space": "image_px", "note": "Laundry inner-wall footprint and corridor doorway"}], "assumptions": ["Deduct the door opening; do not add jamb reveals."]}
BLUEPRINT_ORACLE_JSON
