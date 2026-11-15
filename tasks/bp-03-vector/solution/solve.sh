#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 50.4, "unit": "m", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [711, 684, 966, 879], "space": "pdf_pt", "note": "Multi-Purpose Hall perimeter; folding partition inside"}], "assumptions": ["Measure the perimeter at inner wall faces, deduct perimeter door openings, exclude door reveals. Treat the glazed screen/serving hatch to the Servery as wall below; the folding partition is not a perimeter wall."]}
BLUEPRINT_ORACLE_JSON
