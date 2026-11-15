#!/usr/bin/env python3
"""Render an atomic, reproducible Markdown snapshot of actual evaluation evidence.

No jobs run here. Only public exports, allowlisted replay bundles and named local
diagnostic metadata are read. Pure aggregation/rendering functions are importable.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.export_results import classify, duration, summarize
except ModuleNotFoundError:  # Direct ``python scripts/render_results.py``.
    from export_results import classify, duration, summarize

ROOT = Path(__file__).resolve().parents[1]
PLANNED = (
    ('full-oracle-verified', 'oracle'),
    ('full-nop', 'nop'),
    ('full-deepseek', 'verda/deepseek-4-1-flash-1017'),
    ('full-kimi', 'verda/kimi-k3-1-pro'),
)
DIAGNOSTICS = ('smoke-oracle-v2', 'smoke-no-snapshot', 'smoke-deepseek',
               'smoke-preinstalled', 'smoke-preinstalled-v2', 'full-oracle')
GRADED = ('completed', 'graded_with_warning')
STATUSES = (*GRADED, 'failed', 'missing', 'pending')


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def read_source(root, relative, hashes):
    """Read and hash exactly the bytes parsed, rejecting ambiguous JSON."""
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Source escapes the project root')
    raw = path.read_bytes()

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key in {relative}')
            result[key] = value
        return result

    def finite(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError(f'Non-finite JSON number in {relative}')
        return value

    def reject(_):
        raise ValueError(f'Non-finite JSON number in {relative}')

    value = json.loads(raw, object_pairs_hook=pairs, parse_float=finite, parse_constant=reject)
    hashes[str(relative)] = hashlib.sha256(raw).hexdigest()
    return value


def aggregate(runs):
    """Apply the exporter's exact estimator across an arbitrary set of rows."""
    if not runs:
        raise ValueError('Cannot aggregate an empty group')
    row = summarize([dict(r, model='all', family='all', condition='all') for r in runs])[0]
    durations = [r['duration_sec'] for r in runs if numeric(r.get('duration_sec'))]
    return dict(row, duration_n=len(durations),
                mean_trial_duration_sec=sum(durations) / len(durations) if durations else None)


def validate_matrix(payload, catalog):
    """Reject mixed smoke/old/repeated jobs and incomplete planned exports."""
    if not isinstance(payload, dict) or not isinstance(catalog, list):
        raise ValueError('Expected result object and catalogue array')
    if len(catalog) != 36 or any(not isinstance(t, dict) for t in catalog):
        raise ValueError('The canonical catalogue must contain 36 tasks')
    metadata = {t['id']: t for t in catalog}
    if len(metadata) != 36:
        raise ValueError('Duplicate catalogue task IDs')
    if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', task) for task in metadata):
        raise ValueError('Unsafe catalogue task ID')
    expected = {f'{job}-{task}': (model, task) for job, model in PLANNED for task in metadata}
    runs = payload.get('runs')
    if payload.get('scope') != 'evaluation' or not isinstance(runs, list) or len(runs) != 144:
        raise ValueError('Expected exactly 144 canonical evaluation rows')
    if len({r['id'] for r in runs}) != 144 or {r['id'] for r in runs} != set(expected):
        raise ValueError('Evaluation job IDs differ from the planned matrix')
    for r in runs:
        model, task = expected[r['id']]
        meta = metadata[task]
        if (r['model'], r['task_id'], r['family'], r['condition']) != (
                model, task, meta['family'], meta['condition']):
            raise ValueError(f'Run metadata mismatch: {r["id"]}')
        if r['status'] not in STATUSES:
            raise ValueError('Unknown trial status')
        if r['status'] in GRADED:
            if not numeric(r.get('reward')) or not 0 <= r['reward'] <= 1:
                raise ValueError('Graded trial lacks a valid official reward')
        elif r.get('reward') is not None:
            raise ValueError('Ungraded trial must not supply an official reward')
        if bool(r.get('error_type')) != (r['status'] == 'graded_with_warning') and r['status'] in GRADED:
            raise ValueError('Graded warning status does not match exception')
        for key in ('duration_sec', 'cost_usd'):
            if r.get(key) is not None and (not numeric(r[key]) or r[key] < 0):
                raise ValueError(f'Invalid {key}')
        if r.get('trajectory_url') not in (None, f'/api/runs/{r["id"]}'):
            raise ValueError('Unexpected replay URL')
    if payload.get('status') not in ('partial', 'complete'):
        raise ValueError('Unknown export status')
    if payload['status'] == 'complete' and any(r['status'] == 'pending' for r in runs):
        raise ValueError('Export claims completion with unfinished rows')
    if 'summary' in payload and payload['summary'] != summarize(runs):
        raise ValueError('Export summary disagrees with per-task records')


def select_examples(runs, catalog, bundles):
    """Choose stable, recorded model examples; never infer a trap's cause."""
    selected = dict.fromkeys(('success', 'failure', 'trap'))
    metadata = {t['id']: t for t in catalog}
    for r in sorted(runs, key=lambda r: r['id']):
        if (r.get('agent') != 'opencode' or r.get('model') not in {model for _, model in PLANNED[2:]}
                or r['status'] == 'pending' or r.get('trajectory_url') != f'/api/runs/{r["id"]}'):
            continue
        b = bundles.get(r['id'])
        if b is None:
            continue
        if not isinstance(b, dict) or b.get('format') != 'blueprint-replay-v1':
            raise ValueError('Unsupported replay bundle')
        if not isinstance(b.get('run'), dict) or any(b['run'].get(k) != r.get(k) for k in
                ('id', 'task_id', 'model', 'status', 'reward', 'error_type', 'duration_sec', 'cost_usd')):
            raise ValueError('Replay disagrees with exported official record')
        if not isinstance(b.get('trajectory'), dict):
            raise ValueError('Replay lacks a recorded trajectory')
        score = b.get('score') if b.get('score') is not None else {}
        if not isinstance(score, dict):
            raise ValueError('Malformed replay score')
        saved = b.get('submission')
        submission = saved if isinstance(saved, dict) else None
        value_score = score.get('value_score')
        success = (r['status'] in GRADED and score.get('valid') is True
                   and numeric(value_score) and value_score >= .99)
        # Exporter absence ("Submission missing") can follow infrastructure loss;
        # it does not prove that a malformed model answer was ever saved.
        invalid = (b.get('submission_error') in ('Submission invalid JSON', 'Submission too large')
                   or score.get('valid') is False
                   or (saved is not None and submission is None))
        miss = (score.get('valid') is True and numeric(value_score) and value_score < .99
                and submission is not None and numeric(submission.get('value')))
        outcome = ('Quantity succeeded; recorded evidence/calibration can still reduce total reward.' if success
                   else 'Saved submission invalid; no quantity interpretation is established.' if invalid
                   else 'Recorded numeric/value miss; its cause is not established.' if miss
                   else 'Recorded trap trial; quantity outcome unavailable, no misread is established.')
        item = dict(run=r, metadata=metadata[r['task_id']], submission=submission,
                    score=score, outcome=outcome, replay=f'data/trajectories/{r["id"]}.json')
        if success and selected['success'] is None:
            selected['success'] = item
        if (invalid or miss) and selected['failure'] is None:
            selected['failure'] = item
        if metadata[r['task_id']].get('trap') is True and selected['trap'] is None:
            item = dict(item)
            item['outcome'] = ('Trap quantity succeeded; no misread is established.' if success
                               else 'Trap submission invalid; cause is not established.' if invalid
                               else 'Trap quantity missed; no specific misread is established.' if miss
                               else 'Recorded trap trial; quantity outcome unavailable, no misread is established.')
            selected['trap'] = item
    return selected


def load_diagnostics(root, hashes):
    """Read only named historical trial results, not raw agent logs or credentials."""
    diagnostics = {}
    for name in DIAGNOSTICS:
        directory = root / 'runs/raw' / name
        job_path = directory / 'result.json'
        job = read_source(root, job_path.relative_to(root), hashes) if job_path.exists() else {}
        rows = []
        for path in sorted(directory.glob('*/result.json')):
            trial = read_source(root, path.relative_to(root), hashes)
            reward = ((trial.get('verifier_result') or {}).get('rewards') or {}).get('reward')
            exception = (trial.get('exception_info') or {}).get('exception_type')
            valid = trial.get('reward_valid', not exception) and numeric(reward)
            rows.append(dict(task_id=trial['task_name'].split('/')[-1], reward=reward if valid else None,
                             status=classify(valid, exception, True), error_type=exception,
                             duration_sec=duration(trial.get('started_at'), trial.get('finished_at')),
                             cost_usd=(trial.get('agent_result') or {}).get('cost_usd')))
        diagnostics[name] = dict(trials=rows, expected=job.get('n_total_trials'),
                                 job_duration_sec=duration(job.get('started_at'), job.get('finished_at')))
    config = root / 'configs/evaluation-smoke-no-snapshot.json'
    if config.exists():
        cfg = read_source(root, config.relative_to(root), hashes)
        kwargs = cfg['agents'][0].get('kwargs', {})
        diagnostics['native_config'] = dict(version=kwargs.get('version'),
                                            snapshot=kwargs.get('opencode_config', {}).get('snapshot'))
    return diagnostics


def number(value, digits=6):
    return f'{value:.{digits}f}' if numeric(value) else 'unavailable'


def text(value):
    """Keep untrusted export strings inside their Markdown table/text cell."""
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('`', '&#96;').replace('\n', ' ').replace('\r', ' ')


def render_report(payload, catalog, bundles, diagnostics, hashes, observed_at):
    """Pure Markdown rendering from already loaded source bytes."""
    runs = payload['runs']
    total = aggregate(runs)
    complete = total['pending'] == 0
    manifest = '\n'.join(f'{path}\t{digest}' for path, digest in sorted(hashes.items())) + '\n'
    lines = ['# Results and retained evidence', '',
             '**All planned trials are finished.**' if complete else '**Full evaluation is in progress; no full-set result is claimed.**', '',
             f'Observed at: `{text(observed_at)}`.', '',
             f'This Markdown snapshot reads [data/results.json](data/results.json) (export status `{text(payload["status"])}`, scope `{text(payload["scope"])}`). '
             'The canonical matrix is **144 trials: 36 tasks × four agents/models**. '
             '`full-oracle-verified` is the canonical oracle; interrupted `full-oracle`, smoke jobs and repeats are excluded.', '',
             f'Progress: **{total["completed"]}/{total["n"]} graded**, including **{total["warnings"]} warned**; '
             f'**{total["failed"]} failed/missing**, **{total["pending"]} pending**. Warned trials are included in graded, not clean completions.', '',
             f'Source manifest SHA-256: `{hashlib.sha256(manifest.encode()).hexdigest()}`. '
             'Individual source hashes appear below. The live export can advance after this observation.', '',
             '## Full-set matrix', '',
             '| Job | Agent / model | Expected | Graded | Warned | Failed / missing | Pending | Mean reward | Inference cost USD | Mean recorded trial duration (n) |',
             '|---|---|---:|---:|---:|---:|---:|---:|---|---|']
    for job, model in PLANNED:
        group = [r for r in runs if r['model'] == model]
        if not group:
            continue
        row = aggregate(group)
        lines.append(f'| `{job}` | `{model}` | {row["n"]} | {row["completed"]} | {row["warnings"]} | {row["failed"]} | {row["pending"]} | {number(row["mean_reward"])} | '
                     f'{number(row["cost_usd"])} | {number(row["mean_trial_duration_sec"], 2)} s ({row["duration_n"]}) |')
    lines += ['', 'Means use [the exporter’s `summarize`](scripts/export_results.py): any pending row makes its group mean unavailable. '
              'Once a group finishes, valid official rewards are summed over **all expected tasks**; finished failed/missing trials contribute zero. '
              'A score file does not supply an official reward when the Harbor trial failed. The model means aggregate task rows, not unequal family means.', '',
              'Unknown cost is unavailable (`null`), never zero. Reported inference cost does not establish total Modal infrastructure charges. '
              'Duration means use only rows with a recorded `duration_sec`, derived from trial `started_at`/`finished_at`; the parenthesized count gives coverage. '
              'These can include finished failures. They are not inference-only latency or enclosing job wall time, and concurrent trial durations must not be summed as job wall time.', '',
              '### Family × condition means', '',
              '| Family | Condition | Expected per model | Oracle | No-op | DeepSeek | Kimi |',
              '|---|---|---:|---:|---:|---:|---:|']
    summaries = {(r['model'], r['family'], r['condition']): r for r in summarize(runs)}
    for family, condition in sorted({(t['family'], t['condition']) for t in catalog}):
        expected = sum(t['family'] == family and t['condition'] == condition for t in catalog)
        values = [number(summaries.get((model, family, condition), {}).get('mean_reward')) for _, model in PLANNED]
        lines.append(f'| {text(family)} | {text(condition)} | {expected} | ' + ' | '.join(values) + ' |')
    lines += ['', 'The 36 tasks are **12 paired scenarios on three drawings**, not 36 independent buildings. '
              'The `scan` condition uses synthetic degradation. Scenario train/holdout splits share the three drawings; all scenarios were inspected during curation. '
              'These baseline evaluations train no model weights and cannot establish unseen-building or real-scan generalization.', '',
              '## Recorded model examples', '',
              'Examples require a real exported model result and its allowlisted replay bundle. Selection is deterministic by run ID; '
              'quantity success means recorded `score.value_score >= 0.99`, not necessarily perfect overall reward. No reference quantities are reproduced.']
    for category, item in select_examples(runs, catalog, bundles).items():
        lines += ['', f'### {category.title()}', '']
        if item is None:
            lines += ['Pending: no qualifying recorded model result and allowlisted replay bundle at this snapshot.']
            continue
        r = item['run']; submission = item['submission']; score = item['score']
        lines += [f'[`{text(r["id"])}`]({item["replay"]}) — `{text(r["model"])}`; status `{text(r["status"])}`.', '',
                  f'Question: {text(item["metadata"].get("question", "unavailable"))}', '']
        if submission is None:
            lines += ['Saved submission: unavailable (missing or invalid).']
        else:
            lines += [f'Saved submission: value **{text(json.dumps(submission.get("value")))}**, unit `{text(submission.get("unit", "unavailable"))}`, '
                      f'confidence **{text(json.dumps(submission.get("confidence")))}**.']
        lines += ['', f'Official reward: {number(r.get("reward"))}. Recorded value/evidence/calibration scores: '
                  f'{number(score.get("value_score"))} / {number(score.get("evidence_score"))} / {number(score.get("calibration_score"))}. '
                  f'Weighted contributions: `{text(json.dumps(score.get("components"), sort_keys=True))}`. '
                  f'Exception: `{text(r.get("error_type") or "none")}`.', '', item['outcome']]
    lines += ['', '## Smoke and historical diagnostics — separate from the matrix', '',
              'These rows derive from retained local Harbor trial results. Missing local artifacts remain unavailable. '
              'Reward means cover recorded official rewards only in this diagnostic table, never the canonical expected denominator.', '',
              '| Job | Recorded / expected | Graded | Warned | Failed | Unfinished¹ | Recorded official reward mean (n) | Mean recorded trial duration (n) | Enclosing job elapsed | Cost USD |',
              '|---|---:|---:|---:|---:|---:|---|---|---|---|']
    for name in DIAGNOSTICS:
        info = diagnostics.get(name, {})
        trials = info.get('trials', [])
        rewards = [r['reward'] for r in trials if r['reward'] is not None]
        durations = [r['duration_sec'] for r in trials if numeric(r.get('duration_sec'))]
        expected = info.get('expected')
        graded = sum(r['status'] in GRADED for r in trials)
        warned = sum(r['status'] == 'graded_with_warning' for r in trials)
        costs = [r.get('cost_usd') for r in trials]
        cost = sum(costs) if costs and all(numeric(c) for c in costs) else None
        lines.append(f'| `{name}` | {len(trials)} / {expected if expected is not None else "unavailable"} | {graded} | {warned} | {len(trials)-graded} | '
                     f'{max(0, expected-len(trials)) if numeric(expected) else "unavailable"} | '
                     f'{number(sum(rewards)/len(rewards) if rewards else None)} ({len(rewards)}) | '
                     f'{number(sum(durations)/len(durations) if durations else None, 2)} s ({len(durations)}) | '
                     f'{number(info.get("job_duration_sec"), 2)} s | {number(cost)} |')
    lines += ['', '¹ Unfinished means expected minus retained finished trial records; it does not distinguish running, cancelled or never-started trials. '
              'The stopped original `full-oracle` is diagnostic evidence, not the canonical oracle baseline. '
              'Its verifier timeouts include Modal verifier-log download operations; missing official rewards remain missing even when a score artifact exists.', '',
              'The clean `smoke-no-snapshot` is one check-valve task, not a full-set accuracy estimate. '
              'Its trial duration and reward above come from persisted trial timestamps and verifier results; no informal duration estimate is used. '
              'Warning-bearing smoke rows retain valid rewards when Harbor marks them valid; they are not clean successes.', '',
              'Complete original logs live under `runs/raw/JOB/TRIAL/` on the team machine. These ignored local paths are not GitHub evidence links. '
              'The [clean-smoke config](configs/evaluation-smoke-no-snapshot.json) and '
              '[sanitized retained smoke replay](data/trajectories/smoke-no-snapshot-bp-10-vector.json) remain separate from the active matrix; '
              'a retained smoke bundle need not be allowlisted by the live replay API.', '']
    native = diagnostics.get('native_config', {})
    lines += [f'The recorded clean-smoke configuration uses native OpenCode `{text(native.get("version", "unavailable"))}` '
              f'with `snapshot: {text(json.dumps(native.get("snapshot")))}`. '
              'The symptoms of earlier EPIPE/nonzero exits resemble the primary upstream '
              '[Harbor write-success/EPIPE report](https://github.com/harbor-framework/harbor/issues/4019) and '
              '[OpenCode snapshot/subprocess report](https://github.com/anomalyco/opencode/issues/60447). '
              'The retained clean trial is local evidence for this configuration, not a universal upstream fix. No custom adapter patch is used.', '',
              '## Reproduce this Markdown snapshot', '',
              'After the evaluation owner refreshes the public export, run from any working directory:', '',
              '```sh', 'nice -n 15 python /path/to/afterquery-blueprints/scripts/render_results.py',
              'nice -n 15 python /path/to/afterquery-blueprints/scripts/render_results.py --check', '```', '',
              'The default writes root `RESULTS.md` atomically. `--check` compares substantive content without rewriting; '
              'only the observation timestamp is ignored. Invalid/mixed input or inconsistent replay metadata aborts before replacing the previous report. '
              'No inference, remote calls, export mutation or publication occurs. Source hashes identify exactly the bytes read, including locally available diagnostics.', '',
              '<details>', '<summary>Source SHA-256 manifest</summary>', '', '| Source | SHA-256 |', '|---|---|']
    lines += [f'| `{text(path)}` | `{digest}` |' for path, digest in sorted(hashes.items())]
    lines += ['', '</details>', '']
    return '\n'.join(lines)


def check_report(path, generated):
    def substantive(value):
        return re.sub(r'^Observed at: `[^`]*`\.$', 'Observed at: [ignored].', value, flags=re.MULTILINE)
    return path.exists() and substantive(path.read_text()) == substantive(generated)


def update_report(root=ROOT, *, check=False, observed_at=None):
    root = Path(root)
    hashes = {}
    payload = read_source(root, 'data/results.json', hashes)
    catalog = read_source(root, 'data/catalog.json', hashes)
    validate_matrix(payload, catalog)
    bundles = {}
    for r in payload['runs']:
        if r.get('trajectory_url'):
            relative = f'data/trajectories/{r["id"]}.json'
            bundles[r['id']] = read_source(root, relative, hashes)
    diagnostics = load_diagnostics(root, hashes)
    generated = render_report(payload, catalog, bundles, diagnostics, hashes,
                              observed_at or datetime.now(timezone.utc).isoformat(timespec='seconds'))
    target = root / 'RESULTS.md'
    if check:
        return check_report(target, generated)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=root,
                                         prefix='.RESULTS.md.', suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(generated)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check substantive content without rewriting')
    args = parser.parse_args(argv)
    try:
        current = update_report(check=args.check)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f'Results report not updated: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    if not current:
        print('RESULTS.md differs from the current source snapshot', file=sys.stderr)
        return 1
    print('RESULTS.md matches the current sources' if args.check else 'Updated RESULTS.md from recorded evidence')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
