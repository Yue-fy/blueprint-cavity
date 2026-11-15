"""Generate four PRIVATE optional Harbor tasks, without network or model calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
# Permit both `python -m science_demo.build_tasks` and the documented script path.
sys.path.insert(0, str(HERE.parent))
from science_demo.toy import reference_limit


AGENT_DOCKERFILE = """FROM python:3.12-slim
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git nodejs npm && rm -rf /var/lib/apt/lists/*
RUN npm install -g opencode-ai@1.19.5 && opencode --version
RUN pip install --no-cache-dir numpy==2.2.6
WORKDIR /workspace
COPY input.json /workspace/input.json
"""
VERIFIER_DOCKERFILE = """FROM python:3.12-slim
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
WORKDIR /workspace
COPY . /tests/
"""
VERIFY_SCRIPT = """#!/usr/bin/env python3
# Isolated verifier entry point; only standard-library scoring is imported.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring import main
if __name__ == "__main__":
    raise SystemExit(main())
"""
TEST_SCRIPT = """#!/bin/sh
set -eu
python /tests/verify.py --gold /tests/gold.json --answer /workspace/answer.json --output-dir /logs/verifier
"""


def _json(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _instruction(parameters):
    return f"""# Diagonal coefficient limit

This is a private optional prototype pending independent scientific review and
user approval for public use.

The real parameters are g = {parameters['g']}, c = {parameters['c']},
and A = {parameters['A']}. They are also provided as exact decimal strings in
`/workspace/input.json`.

Define f(u) = A + (1-u)^(3/2), using the branch analytic near u=0
with (1-0)^(3/2)=1. Set E(u,v) = g(c + f(u) + f(v)), and define
F(u,v) = -0.5 * [log(1-E(u,v)) + E(u,v)], using the logarithm branch
analytic at (0,0) and real there. Let a_ii be the coefficient of u^i v^i
in the Taylor expansion of F about (0,0). Let C_i be the coefficient
of u^i in the Taylor expansion of (1-u)^(3/2) about 0.

Determine the limit as i tends to infinity of a_ii / C_i^2.
You may derive the limit or estimate it numerically. Python and NumPy are
available. No external data are needed.

Write one UTF-8 JSON object to `/workspace/answer.json`, with exactly these
three required fields:

- `value`: a finite JSON number giving the limit, or `null` to abstain.
- `confidence`: a finite number between 0 and 1, expressing your probability
  that your numerical answer meets the correctness criterion below.
- `rationale`: a string with your derivation or estimation method. Its content
  is not semantically graded.

The artifact must be at most 1 MiB. Missing files, malformed JSON, duplicate
keys, nonfinite values (including overflowed exponents), and boolean numbers
receive zero total credit.

Numerical credit is 1 for relative error at most 0.001, decreases linearly to
0 at relative error 0.05, and is 0 beyond that. An answer is considered correct
for calibration when its numerical credit is at least 0.99. Calibration credit
is 1 - (confidence - correct)^2, with correct encoded as 0 or 1. The final
reward is 0.90 * numerical credit + 0.10 * calibration credit. Explicitly
abstaining with `value: null` and `confidence: 0` can earn 0.10; a missing
artifact earns 0.
"""


def _config(name):
    return f'''schema_version = "1.4"
artifacts = [{{source = "/workspace/answer.json"}}]

[task]
name = "science-demo/{name}"
version = "0.1.0"
description = "Private optional diagonal coefficient limit prototype"

[metadata]
family = "scientific-limit"
optional = true
private_candidate = true
scientific_review = "pending"
public_use_approval = "pending"

[agent]
timeout_sec = 600

[environment]
build_timeout_sec = 900
cpus = 1
memory_mb = 2048
storage_mb = 4096
network_mode = "public"

[verifier]
timeout_sec = 60
environment_mode = "separate"

[verifier.environment]
build_timeout_sec = 600
cpus = 1
memory_mb = 256
storage_mb = 512
network_mode = "no-network"
'''


def build_tasks(output_dir=HERE / "tasks"):
    """Gold is written only to host-side verifier/oracle paths."""
    rows = json.loads((HERE / "parameters.json").read_text(encoding="utf-8"))
    expected = [f"a-{i:02d}" for i in range(1, 5)]
    if [row["id"] for row in rows] != expected:
        raise ValueError("Expected exactly the four ordered optional parameter cases.")
    output_dir = Path(output_dir)
    names = []
    for row in rows:
        name = "science-" + row["id"]
        parameters = {key: row[key] for key in ("g", "c", "A")}
        reference = reference_limit(**parameters)
        gold = {"value": float(reference), "numerator": reference.numerator,
                "denominator": reference.denominator}
        oracle = {"value": gold["value"], "confidence": 1,
                  "rationale": "Host-only offline reference oracle."}
        files = {
            "instruction.md": _instruction(parameters),
            "task.toml": _config(name),
            "environment/Dockerfile": AGENT_DOCKERFILE,
            "environment/input.json": _json(parameters),
            "tests/Dockerfile": VERIFIER_DOCKERFILE,
            "tests/test.sh": TEST_SCRIPT,
            "tests/verify.py": VERIFY_SCRIPT,
            "tests/scoring.py": (HERE / "scoring.py").read_text(encoding="utf-8"),
            "tests/gold.json": _json(gold),
            "solution/solve.sh": '#!/bin/sh\nset -eu\ncat > "${1:-/workspace/answer.json}" <<\'SCIENCE_ORACLE_JSON\'\n'
                                 + _json(oracle) + "SCIENCE_ORACLE_JSON\n",
        }
        task = output_dir / name
        # Refuse leftover or redirected build inputs instead of retaining an
        # unexpected file in a future Docker context or deleting user files.
        allowed = set(files) | {"environment", "tests", "solution"}
        if task.is_symlink() or any(
            path.is_symlink() or str(path.relative_to(task)) not in allowed
            for path in task.rglob("*")
        ):
            raise ValueError(f"Unsafe existing task context: {task}")
        for relative, contents in files.items():
            path = task / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
            if path.suffix == ".sh":
                path.chmod(0o755)
        names.append(name)
    return names


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "tasks")
    args = parser.parse_args(argv)
    for name in build_tasks(args.output_dir):
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
