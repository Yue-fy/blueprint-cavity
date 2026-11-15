#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 5, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [849.82, 602.681, 875.617, 617.334], "space": "pdf_pt", "note": "CV-1"}, {"page": 0, "bbox": [966.82, 602.681, 992.617, 617.334], "space": "pdf_pt", "note": "CV-2"}, {"page": 0, "bbox": [1084.0, 602.681, 1109.797, 617.334], "space": "pdf_pt", "note": "CV-3"}, {"page": 0, "bbox": [1200.16, 602.681, 1225.97, 617.334], "space": "pdf_pt", "note": "CV-4"}, {"page": 0, "bbox": [1317.1, 602.681, 1342.894, 617.334], "space": "pdf_pt", "note": "CV-5"}], "assumptions": ["Count distinct CV-tagged valve components. A repeated callout does not add another component."]}
BLUEPRINT_ORACLE_JSON
