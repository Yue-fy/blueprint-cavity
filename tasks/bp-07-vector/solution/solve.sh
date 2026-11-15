#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 2, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [675, 995, 710, 1004], "space": "pdf_pt", "note": "Sliding entrance door, inner opening"}, {"page": 0, "bbox": [675, 1032, 710, 1042], "space": "pdf_pt", "note": "Sliding entrance door, outer opening"}], "assumptions": ["Count each sliding door set as one opening, regardless of the number of leaves."]}
BLUEPRINT_ORACLE_JSON
