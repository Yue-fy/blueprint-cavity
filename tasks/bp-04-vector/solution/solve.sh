#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 9.96, "unit": "m", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [841.18, 938.4, 890.08, 967.14], "space": "pdf_pt", "note": "Laundry inner-wall footprint and corridor doorway"}], "assumptions": ["Deduct the door opening; do not add jamb reveals."]}
BLUEPRINT_ORACLE_JSON
