"""API contracts use isolated drawings and the production scorer, never fake scores."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from blueprint_gym.server import create_app

    (tmp_path / "data/previews").mkdir(parents=True)
    (tmp_path / "data/trajectories").mkdir()
    task_root = tmp_path / "tasks/area-vector"
    (task_root / "tests").mkdir(parents=True)
    (task_root / "environment").mkdir()
    (task_root / "environment/drawing.png").write_bytes(b"drawing fixture")
    (tmp_path / "data/previews/area-vector.png").write_bytes(b"preview fixture")
    task = {"id": "area-vector", "scenario_id": "area", "title": "Room area",
            "question": "What is the area?", "family": "room_area", "condition": "vector",
            "difficulty": "medium", "split": "dev", "trap": False,
            "pages": [{"width": 1000, "height": 800, "space": "image_px"}],
            "preview_url": "/api/tasks/area-vector/image", "drawing_filename": "drawing.png",
            "source": {"id": "source", "title": "Fixture", "url": "https://example.org",
                       "license": "CC0", "license_url": "https://example.org/license"}}
    (tmp_path / "data/catalog.json").write_text(json.dumps([task]))
    gold = {"value": 32.05, "unit": "m2", "family": "room_area", "pages": task["pages"]}
    (task_root / "tests/gold.json").write_text(json.dumps(gold))
    with TestClient(create_app(tmp_path)) as api:
        api.fixture_root = tmp_path
        yield api


def answer(value=32.05):
    return {"value": value, "unit": "m2", "confidence": 1,
            "evidence": [{"page": 0, "bbox": [100, 100, 200, 200], "space": "image_px"}],
            "assumptions": []}


def test_public_task_has_no_gold_and_real_score_changes_with_answer(client):
    tasks = client.get("/api/tasks").json()
    assert tasks[0]["id"] == "area-vector"
    assert "value" not in tasks[0] and "gold" not in tasks[0]
    assert client.get("/api/tasks/area-vector").json() == tasks[0]
    exact = client.post("/api/tasks/area-vector/score", json=answer()).json()
    wrong = client.post("/api/tasks/area-vector/score", json=answer(900)).json()
    assert exact["reward"] == 1
    assert wrong["reward"] <= .1
    assert exact["evidence_mode"] == "structural"


@pytest.mark.parametrize("payload", [b"{", b"[]", b"null", b'{"value": NaN}'])
def test_malformed_request_returns_safe_json(client, payload):
    result = client.post("/api/tasks/area-vector/score", content=payload,
                         headers={"content-type": "application/json"})
    assert result.status_code == 400
    assert "error" in result.json()
    assert "Traceback" not in result.text


def test_invalid_answer_has_safe_real_verifier_feedback(client):
    result = client.post("/api/tasks/area-vector/score", json={"value": "oops"})
    assert result.status_code == 200
    assert result.json()["reward"] == 0
    assert result.json()["valid"] is False
    assert result.json()["errors"]


@pytest.mark.parametrize("url", ["/api/tasks/missing", "/api/tasks/..%2F..%2FBRIEF.md/drawing",
                                  "/tasks/area-vector/tests/gold.json", "/.env", "/server.py"])
def test_unknown_and_private_paths_never_expose_files(client, url):
    assert client.get(url).status_code == 404


def test_solution_requires_explicit_human_action(client):
    assert client.get("/api/tasks/area-vector/solution").status_code == 405
    assert client.post("/api/tasks/area-vector/solution", json={}).status_code == 400
    revealed = client.post("/api/tasks/area-vector/solution", json={"reveal": True})
    assert revealed.status_code == 200
    assert revealed.json()["value"] == 32.05


def test_results_pending_and_trajectory_allowlist(client):
    result = client.get("/api/results").json()
    assert result["status"] == "pending"
    assert result["runs"] == result["summary"] == []
    folder = client.fixture_root / "data"
    (folder / "trajectories/run-a.json").write_text('{"events":[]}')
    assert client.get("/api/runs/run-a").status_code == 404
    (folder / "results.json").write_text(json.dumps({"status": "completed", "summary": [],
        "runs": [{"id": "run-a", "trajectory_url": "/api/runs/run-a"}]}))
    assert client.get("/api/runs/run-a").json() == {"events": []}
    assert client.get("/api/runs/..%2Fresults").status_code == 404


def test_preview_drawing_and_only_fixed_static_assets(client):
    assert client.get("/api/tasks/area-vector/image").content == b"preview fixture"
    assert client.get("/api/tasks/area-vector/drawing").content == b"drawing fixture"
    assert client.get("/").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_request_size_and_numeric_overflow_are_bounded(client):
    overflow = client.post("/api/tasks/area-vector/score", content='{"value":1e999}')
    assert overflow.status_code == 400
    oversized = client.post("/api/tasks/area-vector/score", content=b" " * (1024 * 1024 + 1))
    assert oversized.status_code == 413
    assert "error" in oversized.json()


def test_public_allowlist_strips_accidentally_added_private_metadata(client):
    path = client.fixture_root / "data/catalog.json"
    rows = json.loads(path.read_text())
    rows[0]["gold"] = {"value": 12345}
    rows[0]["source"]["secret_annotation"] = 12345
    rows[0]["pages"][0]["answer"] = 12345
    path.write_text(json.dumps(rows))
    public = client.get("/api/tasks").text
    assert "12345" not in public


def test_drawing_and_trajectory_symlinks_cannot_escape_allowlisted_roots(client):
    outside = client.fixture_root / "private.txt"
    outside.write_text("private contents")
    drawing = client.fixture_root / "tasks/area-vector/environment/drawing.png"
    drawing.unlink()
    drawing.symlink_to(outside)
    assert client.get("/api/tasks/area-vector/drawing").status_code == 404
    (client.fixture_root / "data/results.json").write_text(json.dumps({"status": "complete", "summary": [],
        "runs": [{"id": "escape", "trajectory_url": "/api/runs/escape"}]}))
    (client.fixture_root / "data/trajectories/escape.json").symlink_to(outside)
    assert client.get("/api/runs/escape").status_code == 404


@pytest.mark.parametrize("directory,url,filename", [
    ("tasks/area-vector/environment", "/api/tasks/area-vector/drawing", "drawing.png"),
    ("tasks/area-vector", "/api/tasks/area-vector/drawing", "environment/drawing.png"),
    ("tasks", "/api/tasks/area-vector/drawing", "area-vector/environment/drawing.png"),
    ("data/previews", "/api/tasks/area-vector/image", "area-vector.png"),
    ("data/trajectories", "/api/runs/run-a", "run-a.json"),
    ("data", "/api/tasks/area-vector/image", "previews/area-vector.png"),
])
def test_symlinked_asset_directory_or_ancestor_is_rejected(client, directory, url, filename):
    root = client.fixture_root
    (root / "data/results.json").write_text(json.dumps({"status": "complete", "summary": [],
        "runs": [{"id": "run-a", "trajectory_url": "/api/runs/run-a"}]}))
    (root / "data/trajectories/run-a.json").write_text('{"events":[]}')
    target = root / directory
    outside = root.parent / (root.name + "-outside")
    target.rename(outside)
    (outside / filename).write_text('{"sentinel":"outside allowlisted project"}')
    target.symlink_to(outside, target_is_directory=True)
    result = client.get(url)
    assert result.status_code == 404
    assert "sentinel" not in result.text


@pytest.mark.parametrize("payload", [
    '{"value":900,"value":32.05,"unit":"m2","confidence":1,"evidence":[],"assumptions":[]}',
    '{"value":32.05,"unit":"m2","confidence":1,"evidence":[{"page":1,"page":0,"bbox":[100,100,200,200],"space":"image_px"}],"assumptions":[]}',
    '{"value":32.05,"unit":"m2","confidence":1,"evidence":[],"assumptions":[],"extra":{"note":"first","note":"last"}}',
])
def test_duplicate_json_keys_are_rejected_like_offline_verification(client, payload):
    from blueprint_gym.verify import read_json

    path = client.fixture_root / "duplicate-answer.json"
    path.write_text(payload)
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        read_json(path)
    result = client.post("/api/tasks/area-vector/score", content=payload,
                         headers={"content-type": "application/json"})
    assert result.status_code == 400
    assert "error" in result.json()
