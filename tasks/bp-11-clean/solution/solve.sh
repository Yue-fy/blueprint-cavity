#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 5, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [1350.4418, 712.4245, 1391.7599, 736.9479], "space": "image_px", "note": "FP-1"}, {"page": 0, "bbox": [1543.5963, 712.4245, 1584.9144, 736.9479], "space": "image_px", "note": "FP-2"}, {"page": 0, "bbox": [1739.2607, 712.4245, 1780.577, 736.9479], "space": "image_px", "note": "FP-3"}, {"page": 0, "bbox": [1934.925, 712.4245, 1976.243, 736.9479], "space": "image_px", "note": "FP-4"}, {"page": 0, "bbox": [2128.1799, 712.4245, 2169.4979, 736.9479], "space": "image_px", "note": "FP-5"}], "assumptions": ["Count only the FP-tagged fuel pumps; jockey and drain pumps are separate equipment."]}
BLUEPRINT_ORACLE_JSON
