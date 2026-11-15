"""Private optional science package: scorer contract and local Harbor isolation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCORER = ROOT / "science_demo/scoring.py"


def scoring():
    assert SCORER.is_file(), "offline scientific scorer has not been implemented"
    spec = importlib.util.spec_from_file_location("science_scoring", SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def answer(value=10, confidence=1):
    return {"value": value, "confidence": confidence, "rationale": "Derived locally."}


@pytest.mark.parametrize("value, confidence, value_score, calibration, reward", [
    (10, 1, 1, 1, 1),
    (10.01, 1, 1, 1, 1),
    (10.255, 0, .5, 1, .55),
    (10.5, 1, 0, 0, 0),
    (9.5, 0, 0, 1, .1),
    (None, 0, 0, 1, .1),
    (None, 1, 0, 0, 0),
    (10, .5, 1, .75, .975),
])
def test_value_tolerance_and_brier_contract(value, confidence, value_score, calibration, reward):
    result = scoring().score_answer(answer(value, confidence), {"value": 10})
    assert result["value_score"] == pytest.approx(value_score)
    assert result["calibration"] == pytest.approx(calibration)
    assert result["reward"] == pytest.approx(reward)


@pytest.mark.parametrize("bad", [
    None, [], {}, {"value": 10, "confidence": 1},
    answer(True), answer("10"), answer(float("inf")), answer(float("nan")),
    answer(10, True), answer(10, -.1), answer(10, 1.1), answer(10, float("nan")),
    {"value": 10, "confidence": 1, "rationale": None},
])
def test_invalid_or_missing_answer_never_earns_calibration(bad):
    result = scoring().score_answer(bad, {"value": 10})
    assert result["reward"] == 0
    assert result["valid"] is False


@pytest.mark.parametrize("raw", [
    b'', b'not json', b'{}{}', b'[]', b'null', b'\xff',
    b'{"value":10,"value":10,"confidence":1,"rationale":"x"}',
    b'{"value":1e999,"confidence":0,"rationale":"x"}',
    b'{"value":NaN,"confidence":0,"rationale":"x"}',
    b'{"value":Infinity,"confidence":0,"rationale":"x"}',
    b'{"value":10,"confidence":1e999,"rationale":"x"}',
    b'{"value":true,"confidence":0,"rationale":"x"}',
    b'{"value":10,"confidence":true,"rationale":"x"}',
    b'{"value":10,"confidence":1,"rationale":"' + b'x' * (1024 * 1024) + b'"}',
    b'[' * 2000 + b']' * 2000,
])
def test_strict_json_invalid_artifacts_get_zero(tmp_path, raw):
    path = tmp_path / "answer.json"
    path.write_bytes(raw)
    result = scoring().score_file(path, {"value": 10})
    assert result["reward"] == 0
    assert result["valid"] is False


def test_missing_file_differs_from_explicit_abstention(tmp_path):
    module = scoring()
    path = tmp_path / "answer.json"
    assert module.score_file(path, {"value": 10})["reward"] == 0
    path.write_text(json.dumps(answer(None, 0)))
    assert module.score_file(path, {"value": 10})["reward"] == .1


def test_partial_credit_correctness_threshold_controls_brier():
    module = scoring()
    # rel error .00149 gives exactly .99 value score; .0015 falls below.
    assert module.score_answer(answer(10.0148, 1), {"value": 10})["calibration"] == 1
    assert module.score_answer(answer(10.015, 1), {"value": 10})["calibration"] == 0


def test_negative_gold_and_large_numbers_are_bounded():
    module = scoring()
    assert module.score_answer(answer(-10), {"value": -10})["reward"] == 1
    assert module.score_answer(answer(1e308, 0), {"value": -1e308})["reward"] == .1
    assert module.score_answer(answer(10**1000), {"value": 10})["reward"] == 0


def build(tmp_path):
    builder = ROOT / "science_demo/build_tasks.py"
    assert builder.is_file(), "scientific task builder has not been implemented"
    proc = subprocess.run([sys.executable, str(builder), "--output-dir", str(tmp_path)],
                          cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert proc.returncode == 0, proc.stderr
    return sorted(tmp_path.glob("science-a-*"))


def test_four_tasks_parse_as_harbor_and_keep_answer_material_outside_agent_context(tmp_path):
    from harbor.models.task.config import TaskConfig
    tasks = build(tmp_path)
    assert [p.name for p in tasks] == [f"science-a-{i:02d}" for i in range(1, 5)]
    parameters = json.loads((ROOT / "science_demo/parameters.json").read_text())
    for task, params in zip(tasks, parameters):
        config = TaskConfig.model_validate_toml((task / "task.toml").read_text())
        assert config.schema_version == "1.4"
        assert config.agent.timeout_sec == 600
        assert config.environment.cpus == 1
        assert config.environment.memory_mb == 2048
        assert config.verifier.environment_mode.value == "separate"
        assert config.verifier.environment.network_mode.value == "no-network"
        assert config.verifier.timeout_sec <= 60
        assert config.artifacts[0].source == "/workspace/answer.json"
        assert {p.name for p in (task / "environment").iterdir()} == {"Dockerfile", "input.json"}
        assert json.loads((task / "environment/input.json").read_text()) == {
            k: params[k] for k in ("g", "c", "A")}
        docker = (task / "environment/Dockerfile").read_text()
        assert "COPY input.json /workspace/input.json" in docker
        assert "COPY ." not in docker
        public = (task / "instruction.md").read_text() + docker + (task / "task.toml").read_text()
        for hidden in ("reference_limit", "proof.md", "validation.json", "historical", "gold.json", "RESEARCH_CASES"):
            assert hidden not in public
        assert not any(p.is_symlink() for p in task.rglob("*"))
        assert {str(p.relative_to(task)) for p in task.rglob("*") if p.is_file()} == {
            "instruction.md", "task.toml", "environment/Dockerfile", "environment/input.json",
            "tests/Dockerfile", "tests/test.sh", "tests/verify.py", "tests/scoring.py", "tests/gold.json",
            "solution/solve.sh"}
        assert (task / "tests/scoring.py").read_bytes() == SCORER.read_bytes()


def test_generated_oracle_and_offline_verifier_reward_one_noop_zero(tmp_path):
    tasks = build(tmp_path / "tasks")
    for task in tasks:
        artifact = tmp_path / "answer.json"
        subprocess.run(["sh", str(task / "solution/solve.sh"), str(artifact)], check=True, timeout=5)
        for present, expected in ((True, 1), (False, 0)):
            if not present:
                artifact.unlink()
            output = tmp_path / "logs" / task.name / str(present)
            started = time.monotonic()
            proc = subprocess.run([sys.executable, "-I", str(task / "tests/verify.py"),
                "--gold", str(task / "tests/gold.json"), "--answer", str(artifact),
                "--output-dir", str(output)], cwd=tmp_path, env={"PATH": os.defpath},
                capture_output=True, text=True, timeout=5)
            assert proc.returncode == 0, proc.stderr
            assert time.monotonic() - started < 5
            assert float((output / "reward.txt").read_text()) == expected
            assert json.loads((output / "breakdown.json").read_text())["reward"] == expected


def test_historical_error_bound_and_a_zero_control(tmp_path):
    from fractions import Fraction
    tasks = build(tmp_path)
    params = json.loads((ROOT / "science_demo/parameters.json").read_text())
    for task, row in zip(tasks, params):
        g, c, a = (Fraction(row[key]) for key in ("g", "c", "A"))
        # Counterfactual fixture required by the private brief; never agent input.
        historical = float(g * g / (2 * (1 - g * c) ** 2))
        gold = json.loads((task / "tests/gold.json").read_text())
        result = scoring().score_answer(answer(historical), gold)
        if a == 0:
            assert result["reward"] == 1
        else:
            assert result["reward"] <= .1


def test_generation_is_deterministic_and_committed_package_matches(tmp_path):
    tasks = build(tmp_path / "first")
    second = tmp_path / "second"
    build(second)
    for task in tasks:
        for file in task.rglob("*"):
            if file.is_file():
                relative = file.relative_to(tmp_path / "first")
                expected = hashlib.sha256(file.read_bytes()).hexdigest()
                assert hashlib.sha256((second / relative).read_bytes()).hexdigest() == expected
                assert hashlib.sha256((ROOT / "science_demo/tasks" / relative).read_bytes()).hexdigest() == expected


def test_nonregular_and_symlink_answer_paths_do_not_block_verifier(tmp_path):
    module = scoring()
    directory = tmp_path / "directory"
    directory.mkdir()
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    target = tmp_path / "real.json"
    target.write_text(json.dumps(answer()))
    link = tmp_path / "link.json"
    link.symlink_to(target)
    for path in (directory, fifo, link):
        # A blocking FIFO read would time out this independent verifier process.
        gold = tmp_path / "gold.json"
        gold.write_text('{"value":10}')
        output = tmp_path / "output" / path.name
        proc = subprocess.run([sys.executable, str(SCORER), "--gold", str(gold),
            "--answer", str(path), "--output-dir", str(output)], timeout=5,
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert float((output / "reward.txt").read_text()) == 0


def test_generation_refuses_stale_agent_context_or_symlink(tmp_path):
    builder = ROOT / "science_demo/build_tasks.py"
    for kind in ("file", "link"):
        output = tmp_path / kind
        environment = output / "science-a-01/environment"
        environment.mkdir(parents=True)
        if kind == "file":
            (environment / "proof.md").write_text("An old reference must not become agent input.")
        else:
            (environment / "input.json").symlink_to(tmp_path / "elsewhere.json")
        proc = subprocess.run([sys.executable, str(builder), "--output-dir", str(output)],
            cwd=ROOT, text=True, capture_output=True, timeout=10)
        assert proc.returncode != 0
        assert "unsafe existing task context" in proc.stderr.lower()
        assert not (output / "science-a-01/tests/gold.json").exists()
