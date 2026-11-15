#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 26.9, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [943.24, 925.32, 992.14, 1035.84], "space": "pdf_pt", "note": "Fitness room inner-wall footprint"}], "assumptions": ["Net area to inner wall faces."]}
BLUEPRINT_ORACLE_JSON
