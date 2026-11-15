#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 26.9, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [2294.2465, 2250.7574, 2413.1861, 2519.5873], "space": "image_px", "note": "Fitness room inner-wall footprint"}], "assumptions": ["Net area to inner wall faces."]}
BLUEPRINT_ORACLE_JSON
