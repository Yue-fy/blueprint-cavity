#!/usr/bin/env python3
"""Export actual Harbor results; missing and failed trials remain in the denominator."""
import json
import math
import os
import re
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def classify(valid, exception_type, present, job_finished=False):
    if valid:
        return 'graded_with_warning' if exception_type else 'completed'
    return 'failed' if present else ('missing' if job_finished else 'pending')

def summarize(runs):
    groups = defaultdict(list)
    for run in runs:
        groups[(run['model'], run['family'], run['condition'])].append(run)
    rows = []
    for (model, family, condition), group in sorted(groups.items()):
        completed = sum(r['status'] in ('completed', 'graded_with_warning') for r in group)
        warnings = sum(r['status'] == 'graded_with_warning' for r in group)
        pending = sum(r['status'] == 'pending' for r in group)
        costs = [r.get('cost_usd') for r in group]
        rows.append(dict(model=model, family=family, condition=condition, n=len(group),
                         mean_reward=(sum((r.get('reward') or 0) for r in group if r['status'] in ('completed', 'graded_with_warning'))/len(group) if not pending else None),
                         completed=completed, failed=len(group)-completed-pending, pending=pending, warnings=warnings,
                         cost_usd=sum(costs) if all(c is not None for c in costs) else None))
    return rows

def scrub(value, secrets):
    if isinstance(value, dict):
        return {k: ('[REDACTED]' if re.search(r'(?i)(api.?key|token|secret|authorization|password)', k) and not (k.lower().endswith('_tokens') and isinstance(v, (int, float)) and not isinstance(v, bool)) else scrub(v, secrets)) for k, v in value.items()}
    if isinstance(value, list): return [scrub(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets: value = value.replace(secret, '[REDACTED]')
        value = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._~+/-]+', r'\1[REDACTED]', value)
        return value
    return value

def duration(start, end):
    try: return (datetime.fromisoformat(end.replace('Z', '+00:00')) - datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()
    except (ValueError, TypeError, AttributeError): return None

MAX_ARTIFACT_BYTES = 1024 * 1024

def strict_artifact(path):
    """Read bounded, strict JSON without leaking parse errors or file contents."""
    try:
        with path.open('rb') as f:
            data = f.read(MAX_ARTIFACT_BYTES + 1)
        if len(data) > MAX_ARTIFACT_BYTES:
            return None, 'too large'
        def reject_constant(_):
            raise ValueError('Non-finite number')
        def finite_float(text):
            value = float(text)
            if not math.isfinite(value):
                raise ValueError('Non-finite number')
            return value
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('Duplicate key')
                result[key] = value
            return result
        return json.loads(data, parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=unique_pairs), None
    except FileNotFoundError:
        return None, 'missing'
    except (OSError, ValueError, UnicodeDecodeError, RecursionError):
        return None, 'invalid JSON'

def replay_bundle(trial, run, secrets):
    trajectory, _ = strict_artifact(trial/'agent/trajectory.json')
    submission, error = strict_artifact(trial/'artifacts/workspace/answer.json')
    score, _ = strict_artifact(trial/'verifier/breakdown.json')
    return scrub({'format': 'blueprint-replay-v1', 'run': run,
                  'trajectory': trajectory, 'submission': submission, 'score': score,
                  'submission_error': f'Submission {error}' if error else None}, secrets)

def publish_json(path, payload, secrets):
    """Validate and scan before atomically publishing a complete sibling file."""
    text = json.dumps(payload, indent=2, allow_nan=False) + '\n'
    if any(secret in text for secret in secrets):
        raise ValueError('Secret detected in export')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=f'.{path.name}.', suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def export(jobs, *, secrets_file=None):
    if not jobs or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,159}', job) for job in jobs):
        raise ValueError('Provide at least one valid local job name')
    # An optional file is read only when the caller explicitly selects it.
    # The public distribution never searches the author's machine for credentials.
    credentials = {}
    if secrets_file is not None:
        from dotenv import dotenv_values
        credentials = dotenv_values(secrets_file)
    secrets = list({v for source in (credentials, os.environ) for k, v in source.items()
               if v and len(v) >= 8 and re.search(r'(?i)(key|token|secret|password|credential|auth)', k)})
    catalog = {x['id']: x for x in json.loads((ROOT/'data/catalog.json').read_text())}
    runs = []
    dest = ROOT/'data/trajectories'; dest.mkdir(exist_ok=True)
    for job_name in jobs:
        job = ROOT/'runs/raw'/job_name
        config_path = job/'config.json'
        if not config_path.exists(): config_path = ROOT/'configs'/f'evaluation-{job_name}.json'
        config = json.loads(config_path.read_text())
        agent = config['agents'][0]
        model = agent.get('model_name') or agent['name']
        job_result_path = job/'result.json'
        job_finished = bool(json.loads(job_result_path.read_text()).get('finished_at')) if job_result_path.exists() else False
        trials = {}
        for path in job.glob('*/result.json'):
            result = json.loads(path.read_text())
            trials[result['task_name'].split('/')[-1]] = (path, result)
        for task in config['tasks']:
            task_id = Path(task['path']).name
            meta = catalog[task_id]
            item = trials.get(task_id)
            path, result = item if item else (None, {})
            reward = ((result.get('verifier_result') or {}).get('rewards') or {}).get('reward')
            valid = result.get('reward_valid', not result.get('exception_info')) and isinstance(reward, (float, int))
            run_id = f'{job_name}-{task_id}'
            exception_type = (result.get('exception_info') or {}).get('exception_type')
            run = dict(id=run_id, model=model, agent=agent['name'], task_id=task_id,
                family=meta['family'], condition=meta['condition'], reward=reward if valid else None,
                status=classify(valid, exception_type, bool(item), job_finished),
                error_type=exception_type,
                duration_sec=duration(result.get('started_at'), result.get('finished_at')),
                cost_usd=(result.get('agent_result') or {}).get('cost_usd'), trajectory_url=None)
            trajectory = path.parent/'agent/trajectory.json' if path else None
            if trajectory and trajectory.exists():
                bundle = replay_bundle(path.parent, {k: run[k] for k in
                    ('id', 'task_id', 'model', 'status', 'reward', 'error_type', 'duration_sec', 'cost_usd')}, secrets)
                if bundle['trajectory'] is not None:
                    out = dest/f'{run_id}.json'
                    publish_json(out, bundle, secrets)
                    run['trajectory_url'] = f'/api/runs/{run_id}'
            runs.append(run)
    complete = bool(runs) and all(r['status'] in ('completed', 'graded_with_warning', 'failed', 'missing') for r in runs)
    message = ('All exported trials are finished.' if complete else
               'Export is incomplete; means remain unavailable for groups with pending trials.')
    payload = {'status': 'complete' if complete else 'partial',
               'scope': 'smoke' if all('smoke' in name for name in jobs) else 'evaluation',
               'message': message + ' Warnings and errors remain visible. Finished failed or missing trials count as zero; unknown costs are null.', 'runs': runs, 'summary': summarize(runs)}
    publish_json(ROOT/'data/results.json', payload, secrets)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jobs', nargs='+', help='Local runs/raw job names; exporting replaces data/results.json')
    parser.add_argument('--redaction-env', type=Path, help='Explicit optional dotenv file whose values must be redacted')
    args = parser.parse_args()
    export(args.jobs, secrets_file=args.redaction_env)
