"""Judge distribution follows the captured ledger, not directory contents."""
import json
import re

import pytest

from scripts import package_submission as package


def encoded(value):
    return json.dumps(value).encode()


@pytest.fixture
def captured(tmp_path):
    catalog = [{"id": task, "family": family, "condition": condition}
               for task, (family, condition) in package.TASK_IDENTITIES.items()]
    rows = []
    for job, (agent, model) in package.JOBS.items():
        for task, (family, condition) in package.TASK_IDENTITIES.items():
            rows.append({"id": f"{job}-{task}", "agent": agent, "model": model,
                         "task_id": task, "family": family, "condition": condition,
                         "status": "pending", "reward": None, "trajectory_url": None,
                         "error_type": None, "duration_sec": None, "cost_usd": None})
    results = {"scope": "evaluation", "status": "partial", "runs": rows}
    folder = tmp_path / "data/trajectories"
    folder.mkdir(parents=True)
    smoke = {"id": package.SMOKE_ID, "task_id": "bp-10-vector",
             "model": package.JOBS["full-deepseek"][1], "status": "completed",
             "reward": 0.9561428571428572}
    (folder / f"{package.SMOKE_ID}.json").write_bytes(encoded({"format": "blueprint-replay-v1", "run": smoke}))
    row = next(row for row in rows if row["id"] == "full-deepseek-bp-01-vector")
    row.update(status="completed", reward=0.5, trajectory_url=f"/api/runs/{row['id']}")
    bundle = {"format": "blueprint-replay-v1", "run": {
        field: row[field] for field in ("id", "task_id", "model", "status", "reward", "error_type", "duration_sec", "cost_usd")}}
    path = folder / f"{row['id']}.json"
    path.write_bytes(encoded(bundle))
    return tmp_path, results, catalog, row, bundle, path


def collect(captured):
    root, results, catalog, *_ = captured
    return package.collect_replays(root, encoded(results), encoded(catalog))


def test_only_referenced_and_named_smoke_are_opened(captured):
    root, *_ = captured
    folder = root / "data/trajectories"
    # Unreferenced candidates, including out-of-scope names, are never opened.
    (folder / "full-kimi-bp-02-scan.json").write_text("invalid JSON, deliberately unreferenced")
    (folder / "full-deepseek-bp-99-clean.json").write_text("not approved")
    (folder / "full-deepseek-bp-03-clean.json").symlink_to(root / "private-do-not-read")
    assert set(collect(captured)) == {
        f"data/trajectories/{package.SMOKE_ID}.json",
        "data/trajectories/full-deepseek-bp-01-vector.json",
    }


def test_out_of_range_referenced_identity_is_rejected(captured):
    _, _, _, row, *_ = captured
    row.update(id="full-deepseek-bp-99-clean", task_id="bp-99-clean",
               trajectory_url="/api/runs/full-deepseek-bp-99-clean")
    with pytest.raises(ValueError, match="evaluation run identity"):
        collect(captured)


@pytest.mark.parametrize("field,value", [
    ("id", "full-kimi-bp-01-vector"), ("task_id", "bp-02-vector"),
    ("model", "unapproved/model"), ("reward", 0.9), ("status", "pending"),
])
def test_bundle_filename_record_and_ledger_must_match(captured, field, value):
    *_, bundle, path = captured
    bundle["run"][field] = value
    path.write_bytes(encoded(bundle))
    with pytest.raises(ValueError, match=f"Replay/ledger {field} mismatch"):
        collect(captured)


def test_missing_referenced_replay_is_rejected(captured):
    *_, path = captured
    path.unlink()
    with pytest.raises(ValueError, match="Required regular file missing"):
        collect(captured)


def test_missing_ledger_reward_cannot_bypass_replay_comparison(captured):
    _, _, _, row, *_ = captured
    del row["reward"]
    with pytest.raises(ValueError, match="Incomplete evaluation run record"):
        collect(captured)


def test_ledger_family_must_match_approved_task(captured):
    _, _, _, row, *_ = captured
    row["family"] = "piping"
    with pytest.raises(ValueError, match="family/condition mismatch"):
        collect(captured)


def test_duplicate_ledger_row_does_not_replace_missing_identity(captured):
    _, results, *_ = captured
    results["runs"][-1] = results["runs"][0].copy()
    with pytest.raises(ValueError, match="duplicate evaluation run identity"):
        collect(captured)


def test_all_documented_configs_are_required_not_optional(tmp_path, monkeypatch):
    missing = "configs/judge-docker-science-kimi.json"

    def read(_root, name):
        if name == missing:
            raise ValueError(f"Required regular file missing: {name}")
        return b"{}"

    monkeypatch.setattr(package, "_read", read)
    with pytest.raises(ValueError, match=re.escape(missing)):
        package.collect(tmp_path)


def test_distribution_science_commands_have_included_config_dependencies():
    guide = package.PORTABLE_SCIENCE_GUIDE
    names = set(package.CONFIG_FILES + package.SOURCE_FILES)
    commands = re.findall(r"python (scripts/\S+\.py)", guide)
    assert commands and set(commands) <= names
    assert {"blueprint_gym/judge_network.py", "blueprint_gym/judge_agents.py",
            "configs/judge-docker-science-deepseek.json"} <= names
    assert "public networking" in guide
    assert "outbound enforcement" in guide
    assert "unavailable in this distribution" in guide
    assert not re.search(r"\.venv/bin/python\s+science_demo/run_evaluation\.py", guide)


def test_final_recording_and_all_science_job_reproducers_are_included():
    required = {"scripts/record_demo.py", "demo/README.md"} | {
        f"science_demo/evaluations/science-{agent}-four.json"
        for agent in ("deepseek", "kimi", "oracle", "nop")
    }
    assert required <= set(package.SOURCE_FILES)
    # Check the actual referenced sources/configs, not a synthetic missing path.
    for name in required:
        assert package._read(package.ROOT, name)
    demo_commands = re.findall(r"\.venv/bin/python\s+(scripts/\S+\.py)",
                              package._read(package.ROOT, "DEMO.md").decode())
    assert demo_commands and set(demo_commands) <= set(package.SOURCE_FILES)
    for agent in ("deepseek", "kimi", "oracle", "nop"):
        config = json.loads(package._read(package.ROOT,
                            f"science_demo/evaluations/science-{agent}-four.json"))
        assert config["n_concurrent_trials"] == 1
        assert {task["path"] for task in config["tasks"]} == {
            f"science_demo/tasks/science-a-{number:02d}" for number in range(1, 5)
        }
    assert "science_demo/run_evaluation.py" not in package.SOURCE_FILES
    assert "scripts/evaluation_guard.py" not in package.SOURCE_FILES
    assert not any(name.startswith(("dist/", "runs/")) for name in package.SOURCE_FILES)
