#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 7.0, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [841.18, 938.4, 890.08, 967.14], "space": "pdf_pt", "note": "Laundry inner-wall footprint and corridor doorway"}], "assumptions": ["Net area to inner wall faces."]}
BLUEPRINT_ORACLE_JSON
