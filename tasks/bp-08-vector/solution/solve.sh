#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 214.5, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [386, 419, 1489, 1043], "space": "pdf_pt", "note": "Rectangular six-panel slab field, excluding projecting stair bay"}, {"page": 0, "bbox": [974.011, 754.882, 995.477, 769.558], "space": "pdf_pt", "note": "D16"}], "assumptions": ["Measure the six-panel rectangular field only, excluding the projecting stair bay at the lower right. Report gross plan area before deductions for trenches, sumps or pipe penetrations."]}
BLUEPRINT_ORACLE_JSON
