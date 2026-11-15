"""Human demonstration API. Only selected drawing inputs and exports are served.

The verifier's gold files are deliberately outside the static web root. This is
a public human demo surface; future evaluated agents require network isolation.
"""
from __future__ import annotations

import json
import base64
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from blueprint_gym.scoring import score_answer
from blueprint_gym.verify import _finite_float, _reject_constant, _unique_object


ROOT = Path(__file__).resolve().parent.parent
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,159}$")
PUBLIC_FIELDS = ("id", "scenario_id", "title", "question", "family", "condition",
                 "difficulty", "split", "trap", "pages", "preview_url", "source",
                 "drawing_filename")
MAX_BODY = 1024 * 1024


class InlineScripts(HTMLParser):
    """Hash parsed script bodies, including their exact surrounding whitespace."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self.inside = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.inside = True
            self.scripts.append('')

    def handle_endtag(self, tag):
        if tag == 'script': self.inside = False

    def handle_data(self, data):
        if self.inside: self.scripts[-1] += data


def hbn_csp(page):
    parser = InlineScripts()
    parser.feed(page.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n'))
    hashes = ' '.join("'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in parser.scripts)
    return ("default-src 'none'; script-src " + (hashes or "'none'") + "; script-src-attr 'none'; "
            "style-src 'unsafe-inline'; img-src data:; connect-src 'none'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")


def create_app(project_root: Path | str = ROOT) -> FastAPI:
    root = Path(project_root).resolve()
    web = ROOT / "web"
    app = FastAPI(title="Blueprint Takeoff Gym", docs_url=None, redoc_url=None,
                  openapi_url=None)

    @app.exception_handler(HTTPException)
    async def expected_error(_request, exc):
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code,
                            headers=exc.headers)

    @app.middleware("http")
    async def local_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        default_csp = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if request.url.path != '/hbn/' or response.status_code != 200:
            response.headers['Content-Security-Policy'] = default_csp
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def read_json(path):
        try:
            return json.loads(contained_file(path, root).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise HTTPException(503, "The requested data is not available yet.") from None

    def catalog():
        path = root / "data/catalog.json"
        if not path.is_file():
            return []
        rows = read_json(path)
        if not isinstance(rows, list):
            raise HTTPException(503, "The task catalogue is unavailable.")
        public = []
        for row in rows:
            if isinstance(row, dict) and IDENTIFIER.fullmatch(str(row.get("id", ""))):
                task = {key: row[key] for key in PUBLIC_FIELDS if key in row}
                # Source fields and page geometry have fixed public schemas too.
                task["source"] = {k: row.get("source", {}).get(k, "") for k in
                                  ("id", "title", "url", "license", "license_url")}
                task["pages"] = [{k: page[k] for k in ("width", "height", "space") if k in page}
                                 for page in row.get("pages", []) if isinstance(page, dict)]
                public.append(task)
        return public

    def task_for(task_id):
        if not IDENTIFIER.fullmatch(task_id):
            raise HTTPException(404, "Task not found.")
        for task in catalog():
            if task["id"] == task_id:
                return task
        raise HTTPException(404, "Task not found.")

    def contained_file(path, base):
        # Keep the base anchored to the canonical project tree. Resolving a
        # redirected base would move both sides of the containment comparison.
        if not base.is_relative_to(root) or not path.is_relative_to(base):
            raise HTTPException(404, "File not found.")
        directory = root
        for part in path.parent.relative_to(root).parts:
            directory = directory / part
            if directory.is_symlink():
                raise HTTPException(404, "File not found.")
        resolved = path.resolve()
        if not resolved.is_relative_to(base) or not resolved.is_file():
            raise HTTPException(404, "File not found.")
        return resolved

    async def object_body(request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BODY:
                raise HTTPException(413, "Answer exceeds the 1 MiB limit.")
        try:
            parsed = json.loads(body.decode("utf-8"), parse_constant=_reject_constant,
                                parse_float=_finite_float, object_pairs_hook=_unique_object)
            if not isinstance(parsed, dict):
                raise ValueError("Object required")
            return parsed
        except (ValueError, UnicodeError, RecursionError):
            raise HTTPException(400, "Send a JSON object with finite numbers and unique object keys. Include value, unit, "
                                "confidence, evidence, and assumptions.") from None

    def results():
        path = root / "data/results.json"
        if not path.is_file():
            return {"status": "pending", "runs": [], "summary": [],
                    "message": "Model runs have not been exported yet. No performance claims are available."}
        try:
            result = read_json(path)
            if not isinstance(result, dict) or not isinstance(result.get("runs"), list) or not isinstance(result.get("summary"), list):
                raise ValueError
            return result
        except (HTTPException, ValueError):
            return {"status": "unavailable", "runs": [], "summary": [],
                    "message": "The results export is unavailable. Try refreshing after the run completes."}

    @app.get("/api/tasks")
    def list_tasks():
        return catalog()

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str):
        return task_for(task_id)

    @app.get("/api/tasks/{task_id}/image")
    def get_image(task_id: str):
        task_for(task_id)
        base = root / "data/previews"
        return FileResponse(contained_file(base / f"{task_id}.png", base), media_type="image/png")

    @app.get("/api/tasks/{task_id}/drawing")
    def get_drawing(task_id: str):
        task = task_for(task_id)
        filename = task.get("drawing_filename", "")
        if filename not in ("drawing.png", "drawing.pdf", "drawing.jpg", "drawing.jpeg"):
            raise HTTPException(404, "Drawing not found.")
        base = root / "tasks" / task_id / "environment"
        return FileResponse(contained_file(base / filename, base), filename=filename,
                            content_disposition_type="inline")

    @app.post("/api/tasks/{task_id}/score")
    async def score(task_id: str, request: Request):
        task_for(task_id)
        answer = await object_body(request)
        gold = read_json(root / "tasks" / task_id / "tests/gold.json")
        return score_answer(answer, gold)

    @app.post("/api/tasks/{task_id}/solution")
    async def solution(task_id: str, request: Request):
        task_for(task_id)
        body = await object_body(request)
        if body.get("reveal") is not True:
            raise HTTPException(400, "Explicit human reveal required: send reveal: true.")
        return read_json(root / "tasks" / task_id / "tests/gold.json")

    @app.get("/api/results")
    def get_results():
        return results()

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str):
        if not IDENTIFIER.fullmatch(run_id):
            raise HTTPException(404, "Run not found.")
        exported = next((run for run in results()["runs"]
                         if isinstance(run, dict) and run.get("id") == run_id and
                         run.get("trajectory_url") in (f"/api/runs/{run_id}",
                             f"data/trajectories/{run_id}.json", f"/data/trajectories/{run_id}.json")), None)
        if exported is None:
            raise HTTPException(404, "Exported trajectory not found.")
        base = root / "data/trajectories"
        return read_json(contained_file(base / f"{run_id}.json", base))

    @app.get("/")
    def index():
        return FileResponse(web / "index.html", media_type="text/html")

    @app.api_route('/film/', methods=['GET', 'HEAD'])
    def film_page():
        return FileResponse(web / 'film.html', media_type='text/html')

    @app.api_route('/submit/', methods=['GET', 'HEAD'])
    def submission_page():
        return FileResponse(web / 'submit.html', media_type='text/html')

    @app.api_route('/downloads/{filename}', methods=['GET', 'HEAD'])
    def submission_download(filename: str):
        types = {
            'blueprint-cavity-submission.zip': 'application/zip',
            'youtube-thumbnail.jpg': 'image/jpeg',
            'cover-square.jpg': 'image/jpeg',
            'captions.en.srt': 'application/x-subrip',
            'youtube-title.txt': 'text/plain',
            'youtube-description.txt': 'text/plain',
            'submission.en.txt': 'text/plain',
            'README.zh-CN.txt': 'text/plain',
            'CREDITS.txt': 'text/plain',
            'judge-walkthrough.zh-CN.pdf': 'application/pdf',
        }
        if filename not in types: raise HTTPException(404, 'File not found.')
        base = root / 'public_submission'
        path = base / filename
        if path.is_symlink(): raise HTTPException(404, 'File not found.')
        return FileResponse(contained_file(path, base), media_type=types[filename],
                            filename=filename, content_disposition_type='attachment',
                            headers={'Cache-Control': 'no-store'})

    @app.api_route('/guide/', methods=['GET', 'HEAD'])
    def product_guide():
        path = root / 'public_delivery/product-manual.zh-CN.pdf'
        if path.is_symlink(): raise HTTPException(404, 'File not found.')
        return FileResponse(contained_file(path, root / 'public_delivery'),
                            media_type='application/pdf', headers={'Cache-Control': 'no-store'})

    @app.api_route('/media/{filename}', methods=['GET', 'HEAD'])
    def film_media(filename: str):
        types = {'blueprint-film.mp4': 'video/mp4', 'blueprint-film.vtt': 'text/vtt',
                 'blueprint-poster.jpg': 'image/jpeg'}
        if filename not in types: raise HTTPException(404, 'File not found.')
        path = root / 'public_delivery' / filename
        if path.is_symlink(): raise HTTPException(404, 'File not found.')
        return FileResponse(contained_file(path, root / 'public_delivery'),
                            media_type=types[filename], headers={'Cache-Control': 'no-store'})

    @app.api_route('/hbn/', methods=['GET', 'HEAD'])
    def hbn_page(request: Request):
        path = root / 'hbn_demo/index.html'
        if path.is_symlink(): raise HTTPException(404, 'File not found.')
        content = contained_file(path, root / 'hbn_demo').read_bytes()
        return Response(content if request.method == 'GET' else b'', media_type='text/html', headers={
            'Content-Security-Policy': hbn_csp(content), 'Cache-Control': 'no-store',
            'Content-Length': str(len(content)),
        })

    @app.get("/style.css")
    def stylesheet():
        return FileResponse(web / "style.css", media_type="text/css")

    @app.get('/cavity-preview.png')
    def cavity_preview():
        return FileResponse(web / 'cavity-preview.png', media_type='image/png')

    @app.get("/app.js")
    def javascript():
        return FileResponse(web / "app.js", media_type="text/javascript")

    @app.get("/replay.js")
    def replay_javascript():
        return FileResponse(web / "replay.js", media_type="text/javascript")

    if (root / "science_demo/validation.json").is_file():
        from science_demo.server import create_app as create_science_app
        app.mount("/science", create_science_app(root))

    return app


app = create_app()
