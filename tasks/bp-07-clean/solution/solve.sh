#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 2, "unit": "count", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [1641.8052, 2420.2477, 1726.9359, 2442.1394], "space": "image_px", "note": "Sliding entrance door, inner opening"}, {"page": 0, "bbox": [1641.8052, 2510.2469, 1726.9359, 2534.5709], "space": "image_px", "note": "Sliding entrance door, outer opening"}], "assumptions": ["Count each sliding door set as one opening, regardless of the number of leaves."]}
BLUEPRINT_ORACLE_JSON
