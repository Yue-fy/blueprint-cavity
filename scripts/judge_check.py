#!/usr/bin/env python3
"""One-command offline scorer audit. Does not launch agents or change results."""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from blueprint_gym.scoring import score_answer as core_score
from blueprint_gym.verify import read_json
from science_demo.scoring import score_file as science_score


def audit(root=ROOT):
    controls=[]
    with tempfile.TemporaryDirectory(prefix='blueprint-judge-') as temp:
        answer_path=Path(temp)/'answer.json'
        for suite, directory in [('core','tasks'),('science','science_demo/tasks')]:
            for task in sorted((root/directory).iterdir()):
                gold_path=task/'tests/gold.json'
                if not gold_path.is_file(): continue
                gold=json.loads(gold_path.read_text())
                if suite=='core':
                    p=gold['pages'][0]
                    reference={'value':gold['value'],'unit':gold['unit'],'confidence':1,
                               'evidence':gold.get('evidence') or [{'page':0,'space':p['space'],'bbox':[1,1,2,2]}],
                               'assumptions':[]}
                    stop={**reference,'value':None,'confidence':0,'evidence':[]}
                else:
                    params=json.loads((task/'environment/input.json').read_text())
                    g,c,a=(Fraction(params[k]) for k in ('g','c','A'))
                    reference={'value':float(g*g/(2*(1-g*(c+2*a))**2)),
                               'confidence':1,'rationale':'Analytic same-input reference.'}
                    stop={**reference,'value':None,'confidence':0}
                wrong={**reference,'value':gold['value']*100+100,'confidence':1}
                fixtures={'reference':json.dumps(reference),'noop':None,'stop_early':json.dumps(stop),
                          'confident_wrong':json.dumps(wrong),'duplicate_keys':'{"value":1,"value":2}',
                          'overflow_number':json.dumps(reference).replace('"value": '+str(reference['value']),'"value": 1e999')}
                row={'suite':suite,'task':task.name}
                for kind,raw in fixtures.items():
                    answer_path.unlink(missing_ok=True)
                    if raw is not None: answer_path.write_text(raw)
                    if suite=='science': value=science_score(answer_path,gold)['reward']
                    else:
                        try: value=core_score(read_json(answer_path),gold)['reward']
                        except (OSError,ValueError,UnicodeError,RecursionError): value=0
                    row[kind]=value
                controls.append(row)
    history={}
    for suite,path in [('core','data/results.json'),('science','science_demo/results.json')]:
        blob=(root/path).read_bytes(); data=json.loads(blob); groups=defaultdict(list)
        for run in data['runs']: groups[run['model']].append(run)
        expected_tasks={r['task'] for r in controls if r['suite']==suite}
        expected_models={'oracle','nop','verda/kimi-k3-1-pro','verda/deepseek-4-1-flash-1017'}
        identities=[r.get('id') if suite=='core' else (r.get('job'),r.get('task_id')) for r in data['runs']]
        unique_ids=len(set(identities))==len(identities) and all(identities)
        model_rows={}
        for model in sorted(expected_models | set(groups)):
            rows=groups[model]
            complete=(len(rows)==len(expected_tasks) and {r['task_id'] for r in rows}==expected_tasks
                      and all(isinstance(r.get('reward'),(int,float)) and not isinstance(r['reward'],bool)
                              and math.isfinite(r['reward']) and 0<=r['reward']<=1
                              and r['status'] in ('completed','graded_with_warning') for r in rows))
            model_rows[model]={'n':len(rows),'expected_n':len(expected_tasks),'complete':complete,
                              'mean_reward':sum(r['reward'] for r in rows)/len(expected_tasks) if complete else None,
                              'warnings':sum(bool(r.get('error_type')) for r in rows)}
        history[suite]={'sha256':hashlib.sha256(blob).hexdigest(),'trials':len(data['runs']),
                       'complete':bool(unique_ids) and set(groups)==expected_models and all(r['complete'] for r in model_rows.values()),
                       'models':model_rows}
    passed=len(controls)==40 and all(r['reference']==1 and r['noop']==0 and
        abs(r['stop_early']-.1)<1e-12 and all(r[k]==0 for k in ('confident_wrong','duplicate_keys','overflow_number')) for r in controls)
    passed=passed and all(h['complete'] for h in history.values())
    return {'kind':'offline-fixture-audit','passed':passed,'controls':controls,'history':history,
            'independent_repeats_completed':False,'training_completed':False,
            'limitations':[
                'Fixture scores are not new Harbor trajectories or three independent model repeats.',
                'Core reference uses privileged gold. Science reference derives its answer from neutral input.',
                'Stop-early is explicit abstention (0.10), not an interrupted model trial.',
                'Core CLI follows symlinks and can block on FIFO; frozen Harbor artifact transfer filters special files. Do not feed untrusted paths to the CLI.',
                'Annotated box overlap is a proxy for evidence; a correct quantity can lose evidence credit.',
                'hBN explorer and published background figure are outside the 160-trial benchmark.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=audit()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(('PASS' if report['passed'] else 'FAIL')+': 40 tasks × 6 offline controls; reference 1, noop 0, stop-early 0.10.')
    for suite,record in report['history'].items():
        print(suite+': '+str(record['trials'])+' historical trials')
        for model,row in record['models'].items():
            mean=f"{row['mean_reward']:.6f}" if row['mean_reward'] is not None else 'INCOMPLETE'
            print(f"  {model}: mean reward {mean}, n={row['n']}/{row['expected_n']}, warnings={row['warnings']}")
    print('Not a new model evaluation. Three-repeat robustness remains unverified.')
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
