#!/usr/bin/env python3
"""Record the actual local app. No HTTP routing, invented outputs, or inference.

Run nice15, one browser, thread counts1; see demo/README.md. Artifacts are ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:8430"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose(api, allow_partial, success_id=None, contrast_id=None):
    results = api.get(ORIGIN + "/api/results").json()
    if results.get("status") == "partial" and not allow_partial:
        raise RuntimeError("Partial export: wait for root confirmation/final export, or explicitly use --allow-partial.")
    tasks = {task["id"]: task for task in api.get(ORIGIN + "/api/tasks").json()}
    exported = [run for run in results.get("runs", []) if run.get("trajectory_url") == f"/api/runs/{run['id']}"]
    candidates = []
    for run in exported:
        reward = run.get("reward")
        if isinstance(reward, (int, float)) and reward >= .85 and run.get("status") in ("completed", "graded_with_warning"):
            bundle = api.get(ORIGIN + run["trajectory_url"]).json()
            answer = bundle.get("submission")
            if isinstance(answer, dict) and answer.get("evidence") and answer.get("value") is not None:
                candidates.append((run, bundle))
    if success_id:
        success = next((item for item in candidates if item[0]["id"] == success_id), None)
    else:
        success = max(candidates, key=lambda item: (item[1]["submission"].get("unit") == "count", item[0]["reward"]), default=None)
    if not success:
        raise RuntimeError("No exported high-scoring run with a saved answer/evidence is available.")
    alternatives = [run for run in exported if run["id"] != success[0]["id"] and (tasks.get(run["task_id"], {}).get("trap") or run.get("reward") is None or run.get("reward", 1) < .2)]
    if contrast_id:
        contrast = next((run for run in alternatives if run["id"] == contrast_id), None)
    else:
        contrast = max(alternatives, key=lambda run: (bool(tasks.get(run["task_id"], {}).get("trap")), run.get("reward") is None, -float(run.get("reward") or 0)), default=None)
    if not contrast:
        raise RuntimeError("No actual weak/failed/trap export is available for the comparison.")
    contrast_bundle = api.get(ORIGIN + contrast["trajectory_url"]).json()
    return results, tasks[success[0]["task_id"]], success, (contrast, contrast_bundle)


def timestamp(seconds):
    millis = round(seconds * 1000)
    return f"{millis // 3600000:02}:{millis // 60000 % 60:02}:{millis // 1000 % 60:02}.{millis % 1000:03}"


def render_captions(cues, measured):
    captions = "WEBVTT\n\n"
    for index, cue in enumerate(cues):
        end = min(cues[index + 1]["start_sec"] if index + 1 < len(cues) else measured, measured)
        if end > cue["start_sec"]:
            captions += f"{timestamp(cue['start_sec'])} --> {timestamp(end)}\n{cue['caption']}\n\n"
    return captions


def duration(path):
    probe = shutil.which("ffprobe")
    if probe:
        output = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, check=True)
        return float(output.stdout.strip())
    bundled = ROOT / ".cache/ms-playwright/ffmpeg-1013/ffmpeg-linux"
    output = subprocess.run([str(bundled), "-threads", "1", "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", output.stderr)
    if not match:
        raise RuntimeError("The recording was saved, but its media duration could not be verified.")
    return int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])


def verify_faststart(path):
    atoms = {}
    with path.open("rb") as stream:
        while header := stream.read(8):
            if len(header) != 8:
                raise ValueError("Truncated MP4 atom")
            start = stream.tell() - 8
            size, kind = struct.unpack(">I4s", header)
            if size == 1:
                size = struct.unpack(">Q", stream.read(8))[0]
            atoms[kind] = start
            if size == 0:
                break
            if size < 8:
                raise ValueError("Invalid MP4 atom")
            stream.seek(start + size)
    return b"moov" in atoms and b"mdat" in atoms and atoms[b"moov"] < atoms[b"mdat"]


def encode_mp4(out):
    """Transcode the accepted recording, without a browser or new capture."""
    encoder, probe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not encoder or not probe:
        raise RuntimeError("MP4 conversion requires existing ffmpeg/ffprobe; this script installs nothing.")
    source, destination = out / "playthrough.webm", out / "playthrough.mp4"
    source_hash = digest(source)
    subprocess.run([encoder, "-hide_banner", "-loglevel", "error", "-y", "-threads", "1", "-filter_threads", "1", "-i", str(source), "-an", "-c:v", "libx264", "-threads", "1", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination)], check=True)
    info = subprocess.run([probe, "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_frames", "-show_entries", "format=duration,size", "-of", "json", str(destination)], capture_output=True, text=True, check=True)
    metadata = json.loads(info.stdout)
    stream = metadata["streams"][0]
    if stream["codec_name"] != "h264" or stream["pix_fmt"] != "yuv420p" or abs(float(metadata["format"]["duration"]) - duration(source)) > .08:
        raise AssertionError("Encoded media did not preserve the required format/duration")
    if digest(source) != source_hash:
        raise AssertionError("Original WebM changed during conversion")
    if not verify_faststart(destination):
        raise AssertionError("MP4 does not have faststart atom order")
    report = {"path": str(destination), "duration_sec": float(metadata["format"]["duration"]), "sha256": digest(destination), "size_bytes": destination.stat().st_size, "source_webm_sha256": source_hash, "stream": stream, "captions": "Separate unchanged playthrough.vtt; no captions/audio burned into the video.", "faststart": True}
    (out / "mp4-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--success-id")
    parser.add_argument("--contrast-id")
    parser.add_argument("--plan", action="store_true", help="Inspect actual export selection without recording.")
    parser.add_argument("--rehearse", action="store_true", help="Check actual UI interactions without timed holds/video.")
    parser.add_argument("--mp4-only", action="store_true", help="Encode the existing WebM to H264/yuv420p/faststart MP4; no new capture.")
    parser.add_argument("--out", type=Path, default=ROOT / "dist/demo")
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / "dist/demo"):
        raise RuntimeError("Recording artifacts must stay under this project's ignored dist/demo directory.")
    out.mkdir(parents=True, exist_ok=True)
    if args.mp4_only:
        encode_mp4(out)
        return
    with sync_playwright() as p:
        api = p.request.new_context()
        results, task, (success, bundle), (contrast, contrast_bundle) = choose(api, args.allow_partial, args.success_id, args.contrast_id)
        source_results_hash = digest(ROOT / "data/results.json")
        selection = {"export_status": results.get("status"), "recorded_exports": sum(bool(run.get("trajectory_url")) for run in results["runs"]), "success": success, "contrast": contrast, "source_task": task["id"]}
        if args.plan:
            print(json.dumps(selection, indent=2))
            api.dispose()
            return
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--renderer-process-limit=1"])
        video_options = {} if args.rehearse else {"record_video_dir": str(out / "raw"), "record_video_size": {"width": 1440, "height": 900}}
        context = browser.new_context(viewport={"width": 1440, "height": 900}, **video_options)
        page = context.new_page()
        started = time.monotonic()
        cues, errors, forbidden = [], [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: forbidden.append(request.url) if not request.url.startswith(ORIGIN + "/") or request.url.endswith("/solution") else None)

        def beat(at, caption):
            wait = at - (time.monotonic() - started)
            if wait > 0 and not args.rehearse:
                page.wait_for_timeout(wait * 1000)
            cues.append({"start_sec": round(time.monotonic() - started, 3), "caption": caption})

        partial = "PARTIAL SNAPSHOT. " if results.get("status") == "partial" else ""
        beat(0, partial + "Actual exported runs and real app interaction. Recorded playback; no live model inference.")
        page.goto(ORIGIN + "/")
        expect(page.locator("#task-count")).to_have_text("36")
        beat(5, f"Source drawing: {task['id']}. The following manual form demonstration reuses a saved model quantity, not an independent human measurement.")
        page.locator(f'[data-task="{task["id"]}"]').click()
        page.wait_for_function("() => state.loaded")
        page.locator("#drawing-stage").scroll_into_view_if_needed()
        beat(11, "Evidence stays in the original drawing coordinate space, independent of preview scale.")
        answer = bundle["submission"]
        box = answer["evidence"][0]
        page.locator(".coordinate-details summary").click()
        for field, value in zip(("box-x0", "box-y0", "box-x1", "box-y1"), box["bbox"]):
            page.locator("#" + field).fill(str(value))
        page.locator("#evidence-note").fill("Demo entry: first evidence region from the actual recorded answer")
        page.locator("#add-coordinate-box").click()
        expect(page.locator("#evidence-count")).to_have_text("1")
        page.locator("#answer-value").fill(str(answer["value"]))
        page.locator("#answer-unit").select_option(answer["unit"])
        page.locator("#answer-assumptions").fill("UI demonstration reusing a recorded model quantity and one recorded evidence region.")
        beat(18, "Current manual-form verifier check: one saved evidence region and the recorded quantity. This is separate from the official run reward.")
        with page.expect_request(f"**/api/tasks/{task['id']}/score") as manual_request:
            page.locator("#submit-answer").click()
        manual_submission = manual_request.value.post_data_json
        expect(page.locator("#score-result")).to_be_visible()
        page.locator("#score-result").scroll_into_view_if_needed()
        page.screenshot(path=str(out / "desktop-manual-check.png"))
        beat(25, f"Actual higher-scoring run: {success['id']}. Official recorded reward {success.get('reward')}; inspect the saved agent trajectory.")
        page.locator('[data-view="results"]').first.click()
        page.locator(f'[data-run="{success["id"]}"]').click()
        expect(page.locator("#replay-position")).to_have_text(f"1 / {len(bundle['trajectory']['steps'])}")
        page.locator("#replay-panel").scroll_into_view_if_needed()
        page.locator("#replay-next").click()
        beat(31, "Readable recorded tool calls and observations. Play advances saved events; it does not start a model.")
        page.locator("#replay-play").click()
        page.wait_for_timeout(2200)
        if page.locator("#replay-play").get_attribute("aria-label") == "Pause recorded steps":
            page.locator("#replay-play").click()
        beat(38, "Recheck sends the complete original saved JSON unchanged to the current verifier, including confidence precision.")
        with page.expect_request(f"**/api/tasks/{task['id']}/score") as request:
            page.locator("#replay-recheck").click()
        if request.value.post_data_json != answer:
            raise AssertionError("Recorded saved answer changed before scoring")
        expect(page.locator("#replay-recheck-result")).to_contain_text("Recheck reward")
        page.locator("#replay-evidence").click()
        page.locator("#replay-source").scroll_into_view_if_needed()
        page.wait_for_function("() => document.querySelector('#replay-source img').complete")
        page.screenshot(path=str(out / "desktop-recorded-evidence.png"))
        beat(47, f"Actual weak, failed, or trap case: {contrast['id']}. Recorded status {contrast.get('status')}, reward {contrast.get('reward')}. Missing answers and warnings remain visible.")
        page.locator(f'[data-run="{contrast["id"]}"]').click()
        expect(page.locator("#replay-position")).to_have_text(f"1 / {len(contrast_bundle['trajectory']['steps'])}")
        page.locator("#replay-progress").focus()
        page.keyboard.press("End")
        page.locator("#replay-panel").scroll_into_view_if_needed()
        page.screenshot(path=str(out / "desktop-contrast-run.png"))
        beat(57, "Separate approved generic physics toy. These are saved numerical checks, not a scientific model-run report.")
        page.locator('[data-view="overview"]').first.click()
        page.locator('a[href="/science/"]').click()
        expect(page.locator("#case-select option")).to_have_count(4)
        page.locator("#case-select").select_option("a-01")
        page.locator("#reveal").click()
        expect(page.locator("#results-heading")).to_be_focused()
        page.locator(".comparison").scroll_into_view_if_needed()
        beat(65, "A = 0 control: agreement is nondiscriminating. This is not a failed trap.")
        page.locator("#case-select").select_option("a-02")
        page.locator("#reveal").click()
        expect(page.locator("#control-note")).to_contain_text("nondiscriminating")
        page.locator("#control-note").scroll_into_view_if_needed()
        beat(71, "Switch between actual saved grids and relative error. Increasing finite-grid error is not evidence against the independently derived exact limit.")
        page.locator("#grid-select").select_option("512")
        page.locator("#view-select").select_option("error")
        page.locator("#plot").scroll_into_view_if_needed()
        page.locator("#plot .data-point").first.focus()
        page.screenshot(path=str(out / "desktop-physics-control.png"))
        beat(80, "End of owner-private review recording.")
        video = page.video
        context.close()
        destination = out / "playthrough.webm"
        if not args.rehearse:
            video.save_as(destination)
            video.delete()
            measured = duration(destination)
            if not 60 <= measured <= 90:
                raise AssertionError(f"Actual media duration {measured}s is outside 60–90 seconds")
        if errors or forbidden:
            raise AssertionError({"page_errors": errors, "forbidden_requests": forbidden})
        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        phone = mobile.new_page()
        phone.goto(ORIGIN + f"/#workspace/{task['id']}")
        phone.wait_for_function("() => state.loaded")
        if not phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"):
            raise AssertionError("Mobile workspace overflow")
        phone.screenshot(path=str(out / "mobile-drawing.png"), full_page=True)
        phone.goto(ORIGIN + "/science/")
        phone.locator("#case-select").select_option("a-02")
        phone.locator("#reveal").click()
        expect(phone.locator("#control-note")).to_contain_text("nondiscriminating")
        phone.locator("#view-select").select_option("error")
        phone.evaluate("() => scrollTo(0,0)")
        if not phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"):
            raise AssertionError("Mobile physics overflow")
        phone.screenshot(path=str(out / "mobile-physics.png"), full_page=True)
        mobile.close()
        browser.close()
        api.dispose()
        if args.rehearse:
            print(json.dumps({"rehearsal": "PASS: actual UI interactions; no timed video was recorded", **selection}, indent=2))
            return
        manifest = {**selection, "source_results_sha256": source_results_hash, "source_results_changed_during_recording": source_results_hash != digest(ROOT / "data/results.json"), "duration_sec": measured, "video_sha256": digest(destination), "source_box": box, "manual_submission": manual_submission, "manual_entry": "Saved model quantity, one saved box, default human-form confidence. Not an independent human measurement.", "saved_answer_recheck_unchanged": True, "inference_started": False, "page_errors": errors, "forbidden_requests": forbidden, "captions": [cue for cue in cues if cue["start_sec"] < measured]}
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (out / "playthrough.vtt").write_text(render_captions(cues, measured))
        print(json.dumps({"path": str(destination), "duration_sec": measured, "sha256": manifest["video_sha256"], "export_status": results.get("status"), "success": success["id"], "contrast": contrast["id"]}, indent=2))


if __name__ == "__main__":
    main()
