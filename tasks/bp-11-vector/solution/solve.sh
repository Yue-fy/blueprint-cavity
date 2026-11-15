#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 5, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [807.1, 425.681, 831.794, 440.334], "space": "pdf_pt", "note": "FP-1"}, {"page": 0, "bbox": [922.54, 425.681, 947.234, 440.334], "space": "pdf_pt", "note": "FP-2"}, {"page": 0, "bbox": [1039.48, 425.681, 1064.173, 440.334], "space": "pdf_pt", "note": "FP-3"}, {"page": 0, "bbox": [1156.42, 425.681, 1181.114, 440.334], "space": "pdf_pt", "note": "FP-4"}, {"page": 0, "bbox": [1271.92, 425.681, 1296.614, 440.334], "space": "pdf_pt", "note": "FP-5"}], "assumptions": ["Count only the FP-tagged fuel pumps; jockey and drain pumps are separate equipment."]}
BLUEPRINT_ORACLE_JSON
