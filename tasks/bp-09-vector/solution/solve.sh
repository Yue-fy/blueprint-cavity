#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 61.69, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [1507, 575, 1858, 1140], "space": "pdf_pt", "note": "150 mm D13 slab footprint"}, {"page": 0, "bbox": [1565.74, 669.861, 1587.222, 684.539], "space": "pdf_pt", "note": "D13"}], "assumptions": ["Report gross plan area of the rectangular slab before deductions for trenches or pipe penetrations."]}
BLUEPRINT_ORACLE_JSON
