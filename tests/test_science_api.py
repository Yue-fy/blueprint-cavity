"""Private scientific sidecar: actual saved data, explicit reveal, strict boundaries."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path):
    from science_demo.server import create_app
    folder = tmp_path / "science_demo"
    folder.mkdir()
    for name in ("validation.json", "parameters.json", "toy.py", "proof.md"):
        shutil.copyfile(ROOT / "science_demo" / name, folder / name)
    with TestClient(create_app(tmp_path)) as api:
        api.fixture_root = tmp_path
        yield api


def test_public_metadata_omits_targets_and_reveal_returns_actual_saved_data(client):
    validation = json.loads((ROOT / "science_demo/validation.json").read_text())
    public = client.get("/api/cases")
    assert public.status_code == 200
    data = public.json()
    assert data["scope"] == "private"
    assert len(data["cases"]) == 4
    for case in data["cases"]:
        assert set(case) <= {"id", "parameters", "grid_size", "compared_grid_size", "indices", "control_nondiscriminating", "domain_bound", "radius", "method"}
    for forbidden in ("reference", "historical_wrong", "ratios", "relative_errors", "coefficients", "proof"):
        assert f'"{forbidden}"' not in public.text
    for actual in validation["cases"]:
        assert str(actual["reference"]["value"]) not in client.get("/").text
        assert str(actual["reference"]["value"]) not in client.get("/app.js").text
        response = client.post(f"/api/cases/{actual['id']}/reveal", json={"reveal": True})
        assert response.status_code == 200
        revealed = response.json()
        assert revealed["case"] == actual
        assert revealed["parameters_sha256"] == validation["parameters_sha256"]
        assert revealed["source_sha256"]["validation.json"] == hashlib.sha256((ROOT / "science_demo/validation.json").read_bytes()).hexdigest()
        assert revealed["limitations"] == validation["limitations"]
        assert "g^2" in revealed["proof"]
        assert revealed["explanation"]["reference_formula"] not in client.get("/app.js").text
        assert revealed["explanation"]["historical_formula"] not in client.get("/").text
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("body", [b"{", b"[]", b"null", b'{"reveal":false}', b'{"reveal":1}', b'{"reveal":true,"extra":0}', b'{"reveal":false,"reveal":true}', b'{"reveal":true,"extra":{"a":1,"a":2}}', b'{"reveal":NaN}', b'{"reveal":1e999}', b'\xff', b" " * 16385])
def test_reveal_requires_strict_bounded_explicit_json(client, body):
    response = client.post("/api/cases/a-01/reveal", content=body)
    assert response.status_code == 400
    assert "error" in response.json()
    assert "Traceback" not in response.text


@pytest.mark.parametrize("path", ["/api/cases/missing/reveal", "/api/cases/..%2Fproof.md/reveal", "/proof.md", "/validation.json", "/parameters.json", "/toy.py", "/.env", "/web/app.js", "/docs"])
def test_unknown_and_private_paths_are_unavailable(client, path):
    response = client.post(path, json={"reveal": True}) if path.endswith("/reveal") else client.get(path)
    assert response.status_code == 404


def test_get_cannot_reveal_and_only_fixed_assets_load(client):
    assert client.get("/api/cases/a-01/reveal").status_code == 405
    for path in ("/", "/app.js", "/style.css"):
        assert client.get(path).status_code == 200


def test_missing_or_redirected_science_data_fails_safely(client, tmp_path):
    path = client.fixture_root / "science_demo/validation.json"
    path.unlink()
    assert client.get("/api/cases").status_code == 503
    assert client.post("/api/cases/a-01/reveal", json={"reveal": True}).status_code == 503
    path.symlink_to(ROOT / "science_demo/validation.json")
    assert client.get("/api/cases").status_code in (404, 503)


@pytest.mark.parametrize("damage", ["json", "method", "duplicate_case", "parameters"])
def test_corrupt_saved_validation_fails_safely(client, damage):
    path = client.fixture_root / "science_demo/validation.json"
    data = json.loads(path.read_text())
    if damage == "json":
        path.write_text("{")
    else:
        if damage == "method":
            del data["method"]
        elif damage == "duplicate_case":
            data["cases"][1] = data["cases"][0]
        else:
            del data["cases"][0]["parameters"]["g"]
        path.write_text(json.dumps(data))
    assert client.get("/api/cases").status_code == 503


@pytest.mark.parametrize("field,value", [
    ("ratios", "invalid"), ("ratios", [1, 2]), ("ratios", [True, 1, 2]),
    ("ratios", [float("inf"), 1, 2]), ("relative_errors", [0]),
    ("coefficients", [1, False, 3]), ("binomial_coefficients", [1, 2]),
    ("indices", [80, True, 120]), ("grid_size", True), ("radius", "0.99"),
    ("reference", {"numerator": 2, "denominator": 225, "value": 0}),
    ("reference", {"numerator": True, "denominator": 225, "value": .1}),
    ("historical_wrong", None), ("historical_relative_error", "bad"),
    ("grid_sensitivity.compared_ratios", None), ("grid_sensitivity.compared_ratios", [1, 2]),
    ("grid_sensitivity.compared_ratios", [1, False, 3]),
    ("grid_sensitivity.compared_grid_size", "512"), ("grid_sensitivity.compared_radius", False),
    ("max_imaginary_ratio", False), ("control_nondiscriminating", 1),
])
def test_malformed_consumed_fields_are_safe_unavailable(client, field, value):
    path = client.fixture_root / "science_demo/validation.json"
    data = json.loads(path.read_text())
    node = data["cases"][0]
    keys = field.split(".")
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    path.write_text(json.dumps(data))
    for response in (client.get("/api/cases"), client.post("/api/cases/a-01/reveal", json={"reveal": True})):
        assert response.status_code == 503
        assert "error" in response.json()


def test_missing_comparison_and_non_utf8_proof_fail_safely(client):
    path = client.fixture_root / "science_demo/validation.json"
    original = path.read_text()
    data = json.loads(original)
    del data["cases"][0]["grid_sensitivity"]["compared_ratios"]
    path.write_text(json.dumps(data))
    assert client.post("/api/cases/a-01/reveal", json={"reveal": True}).status_code == 503
    path.write_text(original)
    (client.fixture_root / "science_demo/proof.md").write_bytes(b"\xff")
    result = client.post("/api/cases/a-01/reveal", json={"reveal": True})
    assert result.status_code == 503 and "error" in result.json()


def test_parent_mount_is_optional_and_scoped(tmp_path):
    from blueprint_gym.server import create_app
    assert TestClient(create_app(tmp_path)).get("/science/").status_code == 404
    shutil.copytree(ROOT / "science_demo", tmp_path / "science_demo", ignore=shutil.ignore_patterns("__pycache__"))
    api = TestClient(create_app(tmp_path))
    assert api.get("/science/").status_code == 200
    assert api.get("/science/api/cases").json()["scope"] == "private"
    assert api.get("/science/proof.md").status_code == 404


def result_export():
    """Complete producer-shaped fixture; protected values must never reach GET."""
    rows = []
    for index in range(1, 5):
        rows.append({"job": "science-deepseek-four", "task_id": f"science-a-{index:02d}",
                     "model": "verda/deepseek-4-1-flash-1017", "status": "pending",
                     "reward": None, "error_type": None, "terminal_reason": None,
                     "launcher_terminal_state": None, "launcher_returncode": None,
                     "duration_sec": None, "cost_usd": None, "input_tokens": None,
                     "output_tokens": None, "submission": {"answer": "PROTECTED_ANSWER"},
                     "score": {"reference": "PROTECTED_REFERENCE"},
                     "raw_trial": "runs/science/PROTECTED_PATH"})
    rows[0].update(status="graded_with_warning", reward=0.0,
                   error_type="AgentTimeoutError", duration_sec=680.5)
    return {"schema_version": 1, "scope": "separate-four-task-generic-case-a",
            "exported_at": "2026-11-15T04:00:00+00:00", "runs": rows,
            "summary": [{"job": "science-deepseek-four", "model": rows[0]["model"],
                         "planned": 4, "graded": 1, "pending": 3,
                         "mean_reward": None, "cost_usd": None}],
            "limitations": ["PROTECTED_ARBITRARY_TEXT"]}


def save_results(client, data):
    path = client.fixture_root / "science_demo/results.json"
    path.write_text(json.dumps(data))
    return path


def test_results_strict_projection_preserves_actual_zero_warning_and_partial_nulls(client):
    data = result_export()
    data["runs"][0]["rationale"] = "PROTECTED_RATIONALE"
    data["summary"][0]["answer"] = "PROTECTED_SUMMARY"
    save_results(client, data)
    response = client.get("/api/results")
    assert response.status_code == 200
    public = response.json()
    assert set(public) == {"available", "exported_at", "runs", "summary"}
    assert public["exported_at"] == "2026-11-15T04:00:00+00:00"
    assert public["available"] is True
    assert set(public["runs"][0]) == {"job", "task_id", "model", "status", "reward", "error_type", "duration_sec", "cost_usd"}
    assert public["runs"][0]["reward"] == 0.0
    assert public["runs"][0]["error_type"] == "AgentTimeoutError"
    assert public["runs"][1]["reward"] is None
    assert public["summary"] == [{"job": "science-deepseek-four", "model": "verda/deepseek-4-1-flash-1017",
                                   "planned": 4, "graded": 1, "pending": 3, "failed": 0,
                                   "missing": 0, "warnings": 1, "mean_reward": None, "cost_usd": None}]
    assert "PROTECTED" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert client.post("/api/results").status_code == 405
    assert client.get("/results.json").status_code == 404


def test_results_finished_failures_remain_in_mean_denominator_and_unknown_cost(client):
    data = result_export()
    for row in data["runs"]:
        row["terminal_reason"] = "launcher_terminal"
        row["launcher_terminal_state"] = "exited"
        row["launcher_returncode"] = 1
    data["runs"][1].update(status="completed", reward=1, duration_sec=10, cost_usd=.2)
    data["runs"][2].update(status="failed", error_type="RuntimeError", duration_sec=4)
    data["runs"][3].update(status="missing")
    data["summary"][0].update(graded=2, pending=0, mean_reward=.25)
    save_results(client, data)
    response = client.get("/api/results")
    assert response.status_code == 200
    assert response.json()["summary"][0] == {
        "job": "science-deepseek-four", "model": "verda/deepseek-4-1-flash-1017",
        "planned": 4, "graded": 2, "pending": 0, "failed": 1, "missing": 1,
        "warnings": 1, "mean_reward": .25, "cost_usd": None}


def test_results_all_finished_rewards_and_known_costs_are_aggregated(client):
    data = result_export()
    for row, reward in zip(data["runs"], [0, .5, 1, 1]):
        row.update(status="completed", error_type=None, reward=reward, duration_sec=2, cost_usd=.1)
    data["summary"][0].update(graded=4, pending=0, mean_reward=.625, cost_usd=.4)
    save_results(client, data)
    summary = client.get("/api/results").json()["summary"][0]
    assert summary["mean_reward"] == .625
    assert summary["cost_usd"] == pytest.approx(.4)
    assert summary["warnings"] == 0


def test_results_missing_is_optional_and_does_not_break_validation(client):
    response = client.get("/api/results")
    assert response.status_code == 200
    assert response.json() == {"available": False, "runs": [], "summary": []}
    assert client.get("/api/cases").status_code == 200


@pytest.mark.parametrize("damage", ["unknown_task", "duplicate_task", "missing_task", "unknown_status",
    "bad_reward", "bool_reward", "reward_on_pending", "no_warning", "bad_duration", "bad_cost",
    "infinite_cost", "bad_model", "mixed_model", "bad_job", "bad_error", "missing_not_terminal",
    "pending_terminal", "bad_schema", "bad_scope", "bad_summary", "duplicate_summary", "no_summary", "bad_timestamp"])
def test_results_malformed_or_inconsistent_exports_fail_closed_without_breaking_explorer(client, damage):
    data = result_export()
    row = data["runs"][0]
    if damage == "unknown_task": row["task_id"] = "science-a-05"
    elif damage == "duplicate_task": data["runs"][1]["task_id"] = row["task_id"]
    elif damage == "missing_task": data["runs"].pop()
    elif damage == "unknown_status": row["status"] = "success"
    elif damage == "bad_reward": row["reward"] = 1.1
    elif damage == "bool_reward": row["reward"] = False
    elif damage == "reward_on_pending": data["runs"][1]["reward"] = 0
    elif damage == "no_warning": row["error_type"] = None
    elif damage == "bad_duration": row["duration_sec"] = -1
    elif damage == "bad_cost": row["cost_usd"] = True
    elif damage == "infinite_cost": row["cost_usd"] = float("inf")
    elif damage == "bad_model": row["model"] = "/private/raw.log"
    elif damage == "mixed_model": data["runs"][1]["model"] = "verda/kimi-k3-1-pro"
    elif damage == "bad_job": row["job"] = "../../private.log"
    elif damage == "bad_error": row["error_type"] = "Exception: raw log secret"
    elif damage == "missing_not_terminal": data["runs"][1]["status"] = "missing"
    elif damage == "pending_terminal": data["runs"][1]["terminal_reason"] = "launcher_terminal"
    elif damage == "bad_schema": data["schema_version"] = True
    elif damage == "bad_scope": data["scope"] = "core144"
    elif damage == "bad_summary": data["summary"][0]["mean_reward"] = .9
    elif damage == "duplicate_summary": data["summary"].append(data["summary"][0])
    elif damage == "no_summary": del data["summary"]
    elif damage == "bad_timestamp": data["exported_at"] = "/raw/logs/secret"
    save_results(client, data)
    response = client.get("/api/results")
    assert response.status_code == 503
    assert response.json() == {"error": "The saved model trial results are unavailable."}
    assert client.get("/api/cases").status_code == 200


@pytest.mark.parametrize("raw", [b"{", b'\xff', b'{"schema_version":1,"schema_version":1}', b"[]", b" " * (2 * 1024 * 1024 + 1)])
def test_results_unreadable_oversized_or_duplicate_json_fails_safely(client, raw):
    (client.fixture_root / "science_demo/results.json").write_bytes(raw)
    assert client.get("/api/results").status_code == 503


def test_results_redirected_file_is_never_followed(client):
    (client.fixture_root / "science_demo/results.json").symlink_to(ROOT / "science_demo/results.json")
    assert client.get("/api/results").status_code == 503
