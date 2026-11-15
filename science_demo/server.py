"""Private review sidecar. Only saved validation is read; no FFT or model is run."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from blueprint_gym.verify import _finite_float, _reject_constant, _unique_object

ROOT = Path(__file__).resolve().parents[1]
FILES = ("validation.json", "parameters.json", "toy.py", "proof.md")


def create_app(project_root: Path | str = ROOT) -> FastAPI:
    root = Path(project_root).resolve()
    folder = root / "science_demo"
    web = ROOT / "science_demo/web"
    app = FastAPI(title="Private scientific candidate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(HTTPException)
    async def expected_error(_request, exc):
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)

    @app.middleware("http")
    async def private_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    def saved(name):
        if name not in FILES or folder.is_symlink():
            raise HTTPException(404, "File not found.")
        path = folder / name
        if path.is_symlink():
            raise HTTPException(404, "File not found.")
        try:
            if path.stat().st_size > 2 * 1024 * 1024:
                raise ValueError
            return path.read_bytes()
        except (OSError, ValueError):
            raise HTTPException(503, "The saved private validation is unavailable.") from None

    def validation():
        def finite(value):
            return type(value) in (int, float) and math.isfinite(value)

        def require(condition):
            if not condition:
                raise ValueError

        def series(value, count):
            return isinstance(value, list) and len(value) == count and all(finite(number) for number in value)

        try:
            data = json.loads(saved("validation.json"), parse_constant=_reject_constant,
                              parse_float=_finite_float, object_pairs_hook=_unique_object)
            if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or len(data["cases"]) != 4:
                raise ValueError
            if {case.get("id") for case in data["cases"] if isinstance(case, dict)} != {"a-01", "a-02", "a-03", "a-04"}:
                raise ValueError
            if not isinstance(data.get("method"), dict) or not isinstance(data.get("definition"), dict) or not isinstance(data.get("limitations"), list):
                raise ValueError
            for key in ("coefficient_extraction", "normalization", "independence", "target_relative_tolerance"):
                if key not in data["method"]:
                    raise ValueError
            if not isinstance(data.get("status"), str) or not isinstance(data.get("parameters_sha256"), str):
                raise ValueError
            require(all(isinstance(data["method"][key], str) for key in ("coefficient_extraction", "normalization", "independence")))
            require(finite(data["method"]["target_relative_tolerance"]) and data["method"]["target_relative_tolerance"] > 0)
            require(all(isinstance(value, str) for value in data["definition"].values()))
            require(all(isinstance(value, str) for value in data["limitations"]))
            for case in data["cases"]:
                if not isinstance(case, dict) or not re.fullmatch(r"a-0[1-4]", str(case.get("id", ""))):
                    raise ValueError
                for key in ("parameters", "indices", "grid_size", "grid_sensitivity", "reference", "ratios", "relative_errors", "control_nondiscriminating", "domain_bound", "radius", "method"):
                    if key not in case:
                        raise ValueError
                if not isinstance(case["parameters"], dict) or not all(isinstance(case["parameters"].get(key), str) for key in ("g", "c", "A")):
                    raise ValueError
                require(all(Decimal(case["parameters"][key]).is_finite() for key in ("g", "c", "A")))
                if not isinstance(case["grid_sensitivity"], dict) or "compared_grid_size" not in case["grid_sensitivity"]:
                    raise ValueError
                require(case["indices"] == [80, 100, 120] and all(type(index) is int for index in case["indices"]))
                require(type(case["grid_size"]) is int and case["grid_size"] == 1024)
                require(type(case["control_nondiscriminating"]) is bool)
                require(isinstance(case["method"], str))
                for key in ("domain_bound", "radius", "max_imaginary_ratio", "historical_wrong", "historical_relative_error"):
                    require(finite(case[key]))
                require(0 <= case["domain_bound"] < 1 and 0 < case["radius"] < 1)
                for key in ("ratios", "relative_errors", "coefficients", "binomial_coefficients"):
                    require(series(case[key], len(case["indices"])))
                reference = case["reference"]
                require(isinstance(reference, dict))
                require(type(reference["numerator"]) is int and type(reference["denominator"]) is int and reference["denominator"] != 0)
                require(finite(reference["value"]) and reference["value"] != 0)
                comparison = case["grid_sensitivity"]
                require(type(comparison["compared_grid_size"]) is int and comparison["compared_grid_size"] == 512)
                require(finite(comparison["compared_radius"]) and 0 < comparison["compared_radius"] < 1)
                require(series(comparison["compared_ratios"], len(case["indices"])))
            return data
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError, InvalidOperation):
            raise HTTPException(503, "The saved private validation is unavailable.") from None

    @app.get("/api/cases")
    def cases():
        data = validation()
        keys = ("id", "parameters", "grid_size", "indices", "control_nondiscriminating", "domain_bound", "radius", "method")
        return {"scope": "private", "status": data["status"],
                "method": {key: data["method"][key] for key in ("coefficient_extraction", "normalization", "independence", "target_relative_tolerance")},
                "cases": [{**{key: case[key] for key in keys if key != "parameters"},
                           "parameters": {key: case["parameters"][key] for key in ("g", "c", "A")},
                           "compared_grid_size": case["grid_sensitivity"]["compared_grid_size"]} for case in data["cases"]]}

    @app.get("/api/results")
    def results():
        """Validate the separate saved export and publish a non-answer projection."""
        unavailable = "The saved model trial results are unavailable."
        path = folder / "results.json"

        def require(condition):
            if not condition:
                raise ValueError

        def numeric(value):
            return type(value) in (int, float) and math.isfinite(value)

        def optional_nonnegative(value):
            return value is None or (numeric(value) and value >= 0)

        try:
            require(not folder.is_symlink() and not path.is_symlink())
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                return {"available": False, "runs": [], "summary": []}
            require(size <= 2 * 1024 * 1024)
            data = json.loads(path.read_bytes(), parse_constant=_reject_constant,
                              parse_float=_finite_float, object_pairs_hook=_unique_object)
            require(isinstance(data, dict) and type(data["schema_version"]) is int and data["schema_version"] == 1)
            require(data["scope"] == "separate-four-task-generic-case-a")
            exported_at = data["exported_at"]
            require(isinstance(exported_at, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00", exported_at))
            datetime.fromisoformat(exported_at)
            require(isinstance(data["runs"], list) and 0 < len(data["runs"]) <= 32)
            require(isinstance(data["summary"], list))
            groups, public = {}, []
            keys = ("job", "task_id", "model", "status", "reward", "error_type", "duration_sec", "cost_usd")
            for row in data["runs"]:
                require(isinstance(row, dict) and all(key in row for key in keys))
                job, task, model = row["job"], row["task_id"], row["model"]
                require(isinstance(job, str) and re.fullmatch(r"science-[a-z0-9][a-z0-9_-]{0,95}", job))
                require(isinstance(task, str) and re.fullmatch(r"science-a-0[1-4]", task))
                require(model in ("verda/deepseek-4-1-flash-1017", "verda/kimi-k3-1-pro", "oracle", "nop"))
                require(row["status"] in ("completed", "graded_with_warning", "failed", "missing", "pending"))
                error = row["error_type"]
                require(error is None or (isinstance(error, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]{0,99}", error)))
                require(optional_nonnegative(row["duration_sec"]) and optional_nonnegative(row["cost_usd"]))
                terminal = row["terminal_reason"]
                require(terminal in (None, "launcher_terminal", "harbor_terminal"))
                graded = row["status"] in ("completed", "graded_with_warning")
                require((numeric(row["reward"]) and 0 <= row["reward"] <= 1) if graded else row["reward"] is None)
                if row["status"] == "completed":
                    require(error is None)
                if row["status"] == "graded_with_warning":
                    require(error is not None)
                if row["status"] == "pending":
                    require(terminal is None and error is None and row["duration_sec"] is None and row["cost_usd"] is None)
                if row["status"] == "missing":
                    require(terminal is not None and error is None and row["duration_sec"] is None)
                group = groups.setdefault(job, [])
                require(all(previous["task_id"] != task and previous["model"] == model
                            and previous["terminal_reason"] == terminal for previous in group))
                group.append(row)
                public.append({key: row[key] for key in keys})
            summaries = []
            require(len(data["summary"]) == len(groups))
            seen = set()
            for summary in data["summary"]:
                require(isinstance(summary, dict))
                job = summary["job"]
                require(isinstance(job, str) and job in groups and job not in seen)
                seen.add(job)
                group = groups[job]
                require({row["task_id"] for row in group} == {f"science-a-{i:02d}" for i in range(1, 5)})
                pending = sum(row["status"] == "pending" for row in group)
                graded = sum(row["status"] in ("completed", "graded_with_warning") for row in group)
                mean = None if pending else sum(row["reward"] or 0 for row in group) / 4
                cost = sum(row["cost_usd"] for row in group) if all(row["cost_usd"] is not None for row in group) else None
                require(optional_nonnegative(cost))
                expected = {"job": job, "model": group[0]["model"], "planned": 4,
                            "graded": graded, "pending": pending, "mean_reward": mean, "cost_usd": cost}
                for key, value in expected.items():
                    actual = summary[key]
                    if key in ("planned", "graded", "pending"):
                        require(type(actual) is int and actual == value)
                    elif key in ("mean_reward", "cost_usd") and value is not None:
                        require(numeric(actual) and math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-12))
                    else:
                        require(actual == value)
                summaries.append({**expected,
                                  "failed": sum(row["status"] == "failed" for row in group),
                                  "missing": sum(row["status"] == "missing" for row in group),
                                  "warnings": sum(row["status"] == "graded_with_warning" for row in group)})
            return {"available": True, "exported_at": exported_at, "runs": public, "summary": summaries}
        except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
            raise HTTPException(503, unavailable) from None

    @app.post("/api/cases/{case_id}/reveal")
    async def reveal(case_id: str, request: Request):
        if not re.fullmatch(r"a-0[1-4]", case_id):
            raise HTTPException(404, "Case not found.")
        data = validation()
        case = next((case for case in data["cases"] if case["id"] == case_id), None)
        if case is None:
            raise HTTPException(404, "Case not found.")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 16384:
                raise HTTPException(400, "Reveal request exceeds the 16 KiB limit.")
        try:
            body = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant,
                              parse_float=_finite_float, object_pairs_hook=_unique_object)
            if not isinstance(body, dict) or set(body) != {"reveal"} or body["reveal"] is not True:
                raise ValueError
        except (ValueError, UnicodeError, RecursionError):
            raise HTTPException(400, "Explicit human reveal required: send exactly {reveal: true} as strict JSON.") from None
        try:
            proof = saved("proof.md").decode("utf-8")
        except UnicodeError:
            raise HTTPException(503, "The saved private proof is unavailable.") from None
        return {"scope": "private", "case": case, "definition": data["definition"], "method": data["method"],
                "explanation": {"reference_formula": "g² / (2[1 − g(c + 2A)]²)",
                                "historical_formula": "g² / (2[1 − gc]²)",
                                "mechanism": "At u = v = 1, q vanishes but f retains A. The full boundary value is E* = g(c + 2A). Expanding around gc while discarding the constant parts loses their contribution to the mixed coefficient. Higher terms containing A must be resummed."},
                "parameters_sha256": data["parameters_sha256"],
                "source_sha256": {name: hashlib.sha256(saved(name)).hexdigest() for name in FILES},
                "limitations": data["limitations"], "proof": proof}

    @app.get("/")
    def index():
        return FileResponse(web / "index.html", media_type="text/html")

    @app.get("/style.css")
    def style():
        return FileResponse(web / "style.css", media_type="text/css")

    @app.get("/app.js")
    def script():
        return FileResponse(web / "app.js", media_type="text/javascript")

    return app
