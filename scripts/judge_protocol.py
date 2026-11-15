#!/usr/bin/env python3
"""Prepare reference + three agent attempts + noop + stop-early in fresh jobs.

Default is offline configuration generation. --execute starts paid model work
and requires the pinned Harbor environment plus Docker or Modal credentials.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from blueprint_gym.judge_network import isolate_protocol_tasks, validate_protocol_destination


def build_configs(root, suite, model, environment, run_id):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,70}',run_id):
        raise ValueError('run-id must be 1–71 letters, digits, hyphens or underscores')
    base=json.loads((root/f'configs/judge-docker-{suite}-{model}.json').read_text())
    base['environment']['type']=environment
    base['jobs_dir']=f'runs/judge/{run_id}'
    base['n_concurrent_trials']=1
    reference=({'import_path':'blueprint_gym.judge_agents:CaseAReferenceAgent'} if suite=='science' else {'name':'oracle'})
    agents=[('reference',reference,1),('agent',base['agents'][0],3),('noop',{'name':'nop'},1),
            ('stop-early',{'import_path':'blueprint_gym.judge_agents:StopEarlyAgent'},1)]
    configs=[]
    for label,agent,attempts in agents:
        config=deepcopy(base)
        config.update(job_name=f'{run_id}-{suite}-{label}',agents=[agent],n_attempts=attempts)
        configs.append(config)
    return configs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['core','science'],default='core')
    parser.add_argument('--model',choices=['kimi','deepseek'],default='kimi')
    parser.add_argument('--environment',choices=['docker','modal'],default='docker')
    parser.add_argument('--run-id',default=datetime.now(timezone.utc).strftime('judge-%Y%m%dT%H%M%S'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    configs=build_configs(ROOT,args.suite,args.model,args.environment,args.run_id)
    output=(args.output or ROOT/f'runs/judge-configs/{args.run_id}').resolve()
    validate_protocol_destination(ROOT, output)
    output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()): parser.error('Output directory must be empty; use a fresh run-id/output.')
    if (ROOT/f'runs/judge/{args.run_id}').exists(): parser.error('Results directory already exists; use a fresh run-id.')
    configs, task_snapshot = isolate_protocol_tasks(ROOT, configs, output)
    commands=[]
    for config in configs:
        path=output/(config['job_name']+'.json')
        path.write_text(json.dumps(config,indent=2)+'\n')
        commands.append([sys.executable,'-m','harbor.cli.main','run','--config',str(path),'--yes'])
    manifest={'status':'prepared_not_executed','suite':args.suite,'model':args.model,
              'trials_planned':len(configs[0]['tasks'])*6,'agent_attempts_per_task':3,
              'reference':'same-input analytic Case A' if args.suite=='science' else 'privileged gold oracle',
              'stop_early':'first observation then explicit abstention, not time-truncated model',
              'commands':commands, 'task_snapshot':task_snapshot}
    manifest_path=output/'protocol.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    if not args.execute:
        print(f'NOT EXECUTED: {manifest["trials_planned"]} trials prepared in {output}')
        print('Use a fresh run-id with --execute to run. Docker route is schema-tested, not engine-tested here.')
        print('New task copies allow only inference.verda.com; actual outbound enforcement remains unverified.')
        return 0
    if not os.environ.get('VERDA_INFERENCE_API_KEY'): parser.error('VERDA_INFERENCE_API_KEY is required for --execute.')
    if args.environment=='modal' and not all(os.environ.get(k) for k in ('MODAL_TOKEN_ID','MODAL_TOKEN_SECRET')):
        parser.error('Modal credentials must be provided through the environment.')
    from harbor.models.job.config import JobConfig
    for config in configs: JobConfig.model_validate(config)
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PYTHONPATH']=str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    manifest['status']='running'; manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    for command in commands:
        result=subprocess.run(['nice','-n','15',*command],cwd=ROOT,env=env)
        if result.returncode:
            manifest['status']='failed'; manifest['failed_command']=command
            manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
            return result.returncode
    manifest['status']='processes_finished_inspect_harbor_results'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Harbor processes finished. Inspect per-trial results and warnings before claiming a gap.')
    return 0


if __name__=='__main__': raise SystemExit(main())
