#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 5, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [1421.921, 1008.6536, 1465.0847, 1033.177], "space": "image_px", "note": "CV-1"}, {"page": 0, "bbox": [1617.6858, 1008.6536, 1660.8494, 1033.177], "space": "image_px", "note": "CV-2"}, {"page": 0, "bbox": [1813.7516, 1008.6536, 1856.9152, 1033.177], "space": "image_px", "note": "CV-3"}, {"page": 0, "bbox": [2008.1108, 1008.6536, 2051.2962, 1033.177], "space": "image_px", "note": "CV-4"}, {"page": 0, "bbox": [2203.7752, 1008.6536, 2246.9338, 1033.177], "space": "image_px", "note": "CV-5"}], "assumptions": ["Count distinct CV-tagged valve components. A repeated callout does not add another component."]}
BLUEPRINT_ORACLE_JSON
