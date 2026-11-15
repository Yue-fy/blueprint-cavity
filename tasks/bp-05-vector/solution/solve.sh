#!/bin/sh
set -eu
mkdir -p /workspace
cat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'
{"value": 22.0, "unit": "m", "confidence": 1.0, "evidence": [{"page": 0, "bbox": [994.24, 767.28, 1068.7, 878.5], "space": "pdf_pt", "note": "Kitchen L-shaped perimeter and door openings; box includes cut-out rooms"}], "assumptions": ["Follow the L-shaped inner perimeter, deduct its door openings, exclude door reveals. Treat the serving hatch as wall below. The Toilet is accessed from Changing, not Kitchen."]}
BLUEPRINT_ORACLE_JSON
