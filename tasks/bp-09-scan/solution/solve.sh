#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 61.69, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [2589.2081, 988.1532, 3192.2685, 1959.1211], "space": "image_px", "note": "150 mm D13 slab footprint"}, {"page": 0, "bbox": [2690.1305, 1151.1744, 2727.0391, 1176.399], "space": "image_px", "note": "D13"}], "assumptions": ["Report gross plan area of the rectangular slab before deductions for trenches or pipe penetrations."]}
BLUEPRINT_ORACLE_JSON
