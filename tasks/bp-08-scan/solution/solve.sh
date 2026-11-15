#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 214.5, "unit": "m2", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [663.1946, 720.0629, 2558.2819, 1792.424], "space": "image_px", "note": "Rectangular six-panel slab field, excluding projecting stair bay"}, {"page": 0, "bbox": [1673.4686, 1297.2853, 1710.3497, 1322.5064], "space": "image_px", "note": "D16"}], "assumptions": ["Measure the six-panel rectangular field only, excluding the projecting stair bay at the lower right. Report gross plan area before deductions for trenches, sumps or pipe penetrations."]}
BLUEPRINT_ORACLE_JSON
