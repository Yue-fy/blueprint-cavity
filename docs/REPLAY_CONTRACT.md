# Recorded-run replay contract

The raw Harbor ATIF stays unchanged in `runs/raw/JOB/TRIAL/agent/trajectory.json`. Publicly served replay files are sanitized bundles, not a claim that custom fields are part of ATIF.

`data/trajectories/RUN_ID.json`:

```json
{
  "format": "blueprint-replay-v1",
  "run": {
    "id": "actual-job-task-id",
    "task_id": "bp-10-vector",
    "model": "provider/model",
    "status": "completed",
    "reward": 0.95,
    "error_type": null,
    "duration_sec": 50,
    "cost_usd": null
  },
  "trajectory": {"schema_version": "ATIF-v1.7", "steps": []},
  "submission": null,
  "score": null,
  "submission_error": null
}
```

The numbers above illustrate field types only; never ship them as result fixtures. `trajectory` is the sanitized actual ATIF object. `submission` is the actual strict-JSON parsed `artifacts/workspace/answer.json`, or null when missing/malformed/oversized. `score` is the actual `verifier/breakdown.json`, or null when unavailable. The official reward/status come from the Harbor trial result; a score file alone must not turn a failed trial into a completed one. Errors contain short safe descriptions. Keep all reward and submission values unchanged; redact credentials while preserving numeric token usage.

The API already allows only exported run IDs present in `data/results.json`. The player must support both this bundle and previously exported bare ATIF. It must tolerate missing fields and malformed/missing saved submissions. All content is treated as untrusted text.

Playback shows recorded events only; it never starts inference. The player may open the corresponding drawing and overlay valid model evidence in canonical coordinates. Recheck uses the original saved JSON against the existing score endpoint, preserving confidence precision. It never calls the human-reference endpoint implicitly.
