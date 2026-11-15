#!/bin/sh
set -eu
python /tests/verify.py --gold /tests/gold.json --answer /workspace/answer.json --output-dir /logs/verifier
