#!/usr/bin/env python3
"""Build a deterministic private judge snapshot from an explicit file allowlist.

No credential files are read. Secret-valued environment variables are compared
with payload bytes in memory; neither values nor matching file contents are logged.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = (
    "README.md", "SUBMISSION.md", "DEMO.md", "DELIVERY.md", "RESULTS.md",
    "LICENSE", "LICENSES.md", "pyproject.toml", "requirements.lock", ".gitignore",
)
SOURCE_FILES = (
    "blueprint_gym/__init__.py", "blueprint_gym/scoring.py",
    "blueprint_gym/verify.py", "blueprint_gym/server.py",
    "web/index.html", "web/cavity-preview.png", "web/film.html", "web/submit.html", "web/app.js", "web/replay.js", "web/style.css",
    "scripts/build_tasks.py", "scripts/serve.sh", "scripts/export_results.py",
    "scripts/render_results.py", "scripts/package_submission.py",
    "scripts/record_demo.py", "demo/README.md",
    "scripts/judge_check.py", "scripts/judge_protocol.py", "blueprint_gym/judge_agents.py", "blueprint_gym/judge_network.py",
    "docs/judge-audit.json",
    "data/authorization.json", "data/catalog.json", "data/scenarios.json",
    "data/sources.json", "data/results.json", "docs/REPLAY_CONTRACT.md",
    "hbn_demo/preview-provenance.json", "hbn_demo/authorization.json",
    "science_demo/authorization.json", "science_demo/ENVIRONMENT.md",
    "science_demo/EVALUATION.md",
    "science_demo/RESULTS.md", "science_demo/results.json",
    "science_demo/evaluations/science-deepseek-four.json",
    "science_demo/evaluations/science-kimi-four.json",
    "science_demo/evaluations/science-oracle-four.json",
    "science_demo/evaluations/science-nop-four.json",
    "science_demo/parameters.json", "science_demo/proof.md",
    "science_demo/toy.py", "science_demo/validate.py", "science_demo/validation.json",
    "science_demo/scoring.py", "science_demo/build_tasks.py", "science_demo/server.py",
    "science_demo/web/index.html", "science_demo/web/app.js", "science_demo/web/style.css",
)
TEST_FILES = tuple(f"tests/{name}.py" for name in (
    "test_scoring", "test_tasks", "test_results", "test_reporting", "test_api",
    "test_science_math", "test_science_tasks", "test_science_api", "test_package_submission", "test_packaging", "test_judge_tools",
))
CONFIG_FILES = tuple(f"configs/{name}.json" for name in (
    "evaluation-smoke-no-snapshot", "evaluation-full-oracle",
    "evaluation-full-oracle-verified", "evaluation-full-nop", "evaluation-full-deepseek",
    "evaluation-full-kimi", "judge-docker-core-oracle", "judge-docker-core-nop",
    "judge-docker-core-deepseek", "judge-docker-core-kimi", "judge-docker-science-deepseek",
    "judge-docker-science-kimi", "judge-docker-science-oracle", "judge-docker-science-nop",
))
TASK_FILES = (
    "instruction.md", "task.toml", "environment/Dockerfile", "tests/Dockerfile",
    "tests/verify.py", "tests/test.sh", "tests/gold.json", "solution/solve.sh",
    "tests/blueprint_gym/__init__.py", "tests/blueprint_gym/scoring.py",
    "tests/blueprint_gym/verify.py",
)
SCIENCE_TASK_FILES = (
    "instruction.md", "task.toml", "environment/Dockerfile", "environment/input.json",
    "tests/Dockerfile", "tests/verify.py", "tests/test.sh", "tests/gold.json",
    "tests/scoring.py", "solution/solve.sh",
)
REPLAY_NAME = re.compile(r"(?:full-(?:deepseek|kimi)|smoke-no-snapshot)-bp-(?:0[1-9]|1[0-2])-(?:vector|clean|scan)\.json\Z")
TASK_FAMILIES = ("area", "area", "skirting", "skirting", "skirting", "openings",
                 "openings", "slab", "slab", "piping", "piping", "piping")
TASK_IDENTITIES = {f"bp-{number:02d}-{condition}": (family, condition)
                   for number, family in enumerate(TASK_FAMILIES, 1)
                   for condition in ("vector", "clean", "scan")}
JOBS = {
    "full-oracle-verified": ("oracle", "oracle"), "full-nop": ("nop", "nop"),
    "full-deepseek": ("opencode", "verda/deepseek-4-1-flash-1017"),
    "full-kimi": ("opencode", "verda/kimi-k3-1-pro"),
}
SMOKE_ID = "smoke-no-snapshot-bp-10-vector"
RUN_FIELDS = ("id", "task_id", "model", "status", "reward", "error_type", "duration_sec", "cost_usd")
PORTABLE_SCIENCE_GUIDE = """# Generic Case A: evaluation distribution

This archive contains a captured science_demo/results.json and RESULTS.md, not
the host-only science_demo/run_evaluation.py or scripts/evaluation_guard.py.
The host runner and its export subcommand are unavailable in this distribution.
Original scientific projects and raw server files remain excluded. The four
science tasks stay separate from the 36-task/144-trial construction benchmark.
The full public product, film and hBN explorer are delivered through the Site;
the evaluation archive does not bundle those large media/research assets.

For a future judge run, install the pinned Python 3.12 requirements and prepare
fresh task copies with restricted agent networking:

```sh
python scripts/judge_protocol.py --suite science --model deepseek --environment docker --run-id judge-science-review
```

The default only prepares configurations. It performs no model call and starts
no container. The generated protocol records source/derived hashes, allows only
inference.verda.com in the agent environment, and preserves the separate
no-network verifier. It plans reference, three model attempts, noop and an
explicit stop-early control. To execute, use a fresh run ID and add --execute;
this starts paid provider work. Supply VERDA_INFERENCE_API_KEY only through the
process environment. The Modal variant also requires MODAL_TOKEN_ID and
MODAL_TOKEN_SECRET. Do not commit credentials. Both backends run one trial at a
time. Docker requires Engine, Compose and supported Harbor egress controls.

The included configs/judge-docker-science-deepseek.json and other original
configs are historical baselines using public networking. Do not run them as
isolated evaluation after the human answer/replay website has been published.
Use the protocol generator so every control receives the same derived tasks.
Actual Docker/Modal outbound enforcement and provider connectivity have not
been tested for this restriction. No configuration alone establishes a result,
and no network restriction rules out previously memorized public answers.

Inspect each resulting Harbor trial and verifier reward before reporting a gap.
Keep original exports unchanged; new runs are separate evidence. No model
weights were post-trained. The project coordinator must review and rebuild any
sanitized export; no host export command is bundled here.
"""
SECRET_NAME = re.compile(r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.I)
SECRET_PATTERN = re.compile(rb"(?:sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")


def _read(root: Path, name: str) -> bytes:
    path = root / name
    # Reject links at every component, even links that resolve inside the root.
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError(f"Symlink rejected: {name}")
    if not path.is_file():
        raise ValueError(f"Required regular file missing: {name}")
    return path.read_bytes()


def collect_replays(root: Path, results_blob: bytes, catalog_blob: bytes) -> dict[str, bytes]:
    """Read only captured-ledger references plus one explicitly approved smoke.

    Unreferenced files are excluded without opening or traversing their names.
    """
    catalog = json.loads(catalog_blob)
    if not isinstance(catalog, list) or len(catalog) != 36:
        raise ValueError("Expected exactly 36 approved catalog tasks")
    seen_tasks = set()
    for task in catalog:
        task_id = task.get("id") if isinstance(task, dict) else None
        if not isinstance(task_id, str) or task_id not in TASK_IDENTITIES or task_id in seen_tasks:
            raise ValueError("Invalid or duplicate catalog task identity")
        if (task.get("family"), task.get("condition")) != TASK_IDENTITIES[task_id]:
            raise ValueError("Catalog task family/condition mismatch")
        seen_tasks.add(task_id)
    results = json.loads(results_blob)
    rows = results.get("runs") if isinstance(results, dict) else None
    if not isinstance(results, dict) or results.get("scope") != "evaluation" or not isinstance(rows, list) or len(rows) != 144:
        raise ValueError("Expected captured 144-trial evaluation ledger")
    expected = {f"{job}-{task}": (task, agent, model) for job, (agent, model) in JOBS.items()
                for task in TASK_IDENTITIES}
    references = {}
    seen_runs = set()
    for row in rows:
        run_id = row.get("id") if isinstance(row, dict) else None
        if not isinstance(run_id, str) or run_id not in expected or run_id in seen_runs:
            raise ValueError("Invalid or duplicate evaluation run identity")
        if not set(RUN_FIELDS + ("agent", "family", "condition", "trajectory_url")).issubset(row):
            raise ValueError("Incomplete evaluation run record")
        task, agent, model = expected[run_id]
        if (row.get("task_id"), row.get("agent"), row.get("model")) != (task, agent, model):
            raise ValueError("Evaluation run/task/model identity mismatch")
        if (row.get("family"), row.get("condition")) != TASK_IDENTITIES[task]:
            raise ValueError("Evaluation task family/condition mismatch")
        seen_runs.add(run_id)
        if row.get("trajectory_url") is not None:
            if agent != "opencode" or row["trajectory_url"] != f"/api/runs/{run_id}":
                raise ValueError("Invalid evaluation replay reference")
            references[run_id] = row
    references[SMOKE_ID] = {"id": SMOKE_ID, "task_id": "bp-10-vector",
                            "model": JOBS["full-deepseek"][1], "status": "completed",
                            "reward": 0.9561428571428572}
    payload = {}
    for run_id, record in sorted(references.items()):
        name = f"data/trajectories/{run_id}.json"
        blob = _read(root, name)
        bundle = json.loads(blob)
        run = bundle.get("run") if isinstance(bundle, dict) else None
        if not isinstance(bundle, dict) or bundle.get("format") != "blueprint-replay-v1" or not isinstance(run, dict):
            raise ValueError(f"Unrecognized sanitized replay: {name}")
        for field in RUN_FIELDS:
            if field in record and run.get(field) != record[field]:
                raise ValueError(f"Replay/ledger {field} mismatch: {name}")
        family, condition = TASK_IDENTITIES[record["task_id"]]
        for field, value in (("family", family), ("condition", condition)):
            if field in run and run[field] != value:
                raise ValueError(f"Replay/ledger {field} mismatch: {name}")
        payload[name] = blob
    return payload


def collect(root: Path) -> dict[str, bytes]:
    """Allow only known paths, fixed task IDs and validated replay filenames."""
    root = root.resolve()
    names = set(TOP_LEVEL + SOURCE_FILES + TEST_FILES)
    names.update(CONFIG_FILES)
    for source in ("dfe-school", "usace-slab", "usace-piping"):
        names.update(f"data/assets/{source}{suffix}" for suffix in (".pdf", "-clean.png", "-scan.png"))
    for number in range(1, 13):
        for condition in ("vector", "clean", "scan"):
            task_id = f"bp-{number:02d}-{condition}"
            names.update(f"tasks/{task_id}/{name}" for name in TASK_FILES)
            names.add(f"tasks/{task_id}/environment/drawing.{'pdf' if condition == 'vector' else 'png'}")
            names.add(f"data/previews/{task_id}.png")
    for number in range(1, 5):
        names.update(f"science_demo/tasks/science-a-{number:02d}/{name}" for name in SCIENCE_TASK_FILES)
    payload = {name: _read(root, name) for name in sorted(names)}
    payload.update(collect_replays(root, payload["data/results.json"], payload["data/catalog.json"]))
    # The distribution documents only executables included and reviewed here.
    payload["science_demo/EVALUATION.md"] = PORTABLE_SCIENCE_GUIDE.encode()
    return payload


def scan(payload: dict[str, bytes], environment: dict[str, str] | None = None) -> int:
    """Fail closed without including matching values or contents in errors."""
    environment = os.environ if environment is None else environment
    secrets = {v.encode() for k, v in environment.items() if SECRET_NAME.search(k) and len(v) >= 8}
    for name, blob in payload.items():
        if SECRET_PATTERN.search(blob) or any(value in blob for value in secrets):
            raise ValueError(f"Secret scan rejected payload file: {name}")
    return len(secrets)


def archive_bytes(payload: dict[str, bytes]) -> bytes:
    """Stable order, ownership, modes, tar timestamps and gzip header."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=6) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, blob in sorted(payload.items()):
                entry = tarfile.TarInfo(f"blueprint-takeoff-gym/{name}")
                entry.size = len(blob)
                entry.mode = 0o755 if name.endswith(".sh") else 0o644
                entry.mtime = entry.uid = entry.gid = 0
                archive.addfile(entry, io.BytesIO(blob))
    return buffer.getvalue()


def snapshot_metadata(core: dict, science: dict) -> dict:
    """Describe captured ledgers without implying external delivery approval."""
    runs = core.get("runs", [])
    science_runs = science.get("runs", [])
    return {"snapshot_status": "captured evaluation snapshot",
            "evaluation_status": core.get("status", "unknown"),
            "exported_trial_rows": len(runs),
            "pending_trials": sum(row.get("status") == "pending" for row in runs),
            "science_exported_trial_rows": len(science_runs),
            "science_pending_trials": sum(row.get("status") == "pending" for row in science_runs)}


def build(root: Path, output_dir: Path) -> dict:
    payload = collect(root)
    checked_secrets = scan(payload)
    results = json.loads(payload["data/results.json"])
    science = json.loads(payload["science_demo/results.json"])
    manifest = {
        "format": "blueprint-private-judge-snapshot-v1",
        "audience": "private owner/judge review; no public publication implied",
        **snapshot_metadata(results, science),
        "core_tasks": 36, "generic_case_a_tasks": 4,
        "canonical_expected_trials": 144,
        "weights_posttrained": False,
        "raw_logs_included": False,
        "replay_selection": "captured canonical ledger references plus named clean smoke; unreferenced files excluded",
        "science_evaluation_guide": "distribution-specific portable commands; host-only runner excluded",
        "secret_scan": {"inherited_secret_values_checked": checked_secrets, "result": "passed"},
        "files": {name: {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)} for name, blob in payload.items()},
    }
    manifest_blob = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    payload["MANIFEST.json"] = manifest_blob
    checksums = "".join(f"{hashlib.sha256(blob).hexdigest()}  {name}\n" for name, blob in sorted(payload.items()))
    payload["MANIFEST.sha256"] = checksums.encode()
    scan(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not (root / ".gitignore").exists() or "dist/" not in (root / ".gitignore").read_text().splitlines():
        raise ValueError("dist/ must be ignored before packaging")
    archive = archive_bytes(payload)
    name = "blueprint-takeoff-gym-private-snapshot.tar.gz"
    # Publish only completely built and scanned bytes.
    with tempfile.NamedTemporaryFile(dir=output_dir, delete=False) as temp:
        temp.write(archive)
        temporary = Path(temp.name)
    temporary.replace(output_dir / name)
    (output_dir / "MANIFEST.json").write_bytes(manifest_blob)
    digest = hashlib.sha256(archive).hexdigest()
    (output_dir / f"{name}.sha256").write_text(f"{digest}  {name}\n")
    return {"archive": str(output_dir / name), "sha256": digest, "files": len(payload),
            "bytes": len(archive), "snapshot_status": manifest["snapshot_status"],
            "inherited_secret_values_checked": checked_secrets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.output_dir.resolve()), indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Packaging refused: {exc}\n")


if __name__ == "__main__":
    main()
