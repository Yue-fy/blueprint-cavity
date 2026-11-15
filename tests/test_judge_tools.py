"""Judge controls must exercise real scorers without rewriting captured evidence."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
import tomllib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class JudgeToolsTests(unittest.TestCase):
    def test_network_derivative_preserves_core_bytes_and_rejects_unsafe_sources(self):
        from scripts.judge_protocol import build_configs
        from blueprint_gym.judge_network import isolate_protocol_tasks
        from harbor.models.task.config import TaskConfig
        for unsafe in (None,'symlink','fifo','phase-override','verifier-public','unreviewed-provider'):
            with self.subTest(unsafe=unsafe),tempfile.TemporaryDirectory() as d:
                root=Path(d); source=root/'tasks/bp-01-clean'
                shutil.copytree(ROOT/'tasks/bp-01-clean',source)
                configs=build_configs(ROOT,'core','kimi','docker','restricted-core')
                for c in configs: c['tasks']=[{'path':'tasks/bp-01-clean'}]
                output=root/'generated';output.mkdir()
                if unsafe=='symlink': (source/'linked.json').symlink_to(source/'tests/gold.json')
                elif unsafe=='fifo': os.mkfifo(source/'pipe')
                elif unsafe in ('phase-override','verifier-public'):
                    path=source/'task.toml';text=path.read_text()
                    text=(text.replace('[agent]','[agent]\nnetwork_mode = "public"') if unsafe=='phase-override'
                          else text.replace('network_mode = "no-network"','network_mode = "public"'))
                    path.write_text(text)
                elif unsafe=='unreviewed-provider':configs[1]['agents'][0]['base_url']='https://public-answer-site.example/v1'
                if unsafe:
                    with self.assertRaises(ValueError): isolate_protocol_tasks(root,configs,output)
                    self.assertFalse((output/'tasks').exists())
                    continue
                derived,manifest=isolate_protocol_tasks(root,configs,output)
                task=Path(derived[0]['tasks'][0]['path'])
                cfg=TaskConfig.model_validate_toml((task/'task.toml').read_text())
                self.assertEqual(cfg.environment.allowed_hosts,['inference.verda.com'])
                self.assertEqual(cfg.verifier.environment.network_mode.value,'no-network')
                for row in manifest['tasks']:
                    self.assertEqual({n for n,h in row['files'].items() if h['source_sha256']!=h['derived_sha256']},{'task.toml'})
                gold=source/'tests/gold.json';before=gold.read_bytes()
                (task/'tests/gold.json').write_text('derivative-only change')
                self.assertEqual(gold.read_bytes(),before)

    def test_network_derivative_refuses_destination_inside_frozen_task_tree(self):
        from scripts.judge_protocol import build_configs
        from blueprint_gym.judge_network import isolate_protocol_tasks
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'tasks/bp-01-clean'
            shutil.copytree(ROOT/'tasks/bp-01-clean',source)
            configs=build_configs(ROOT,'core','kimi','docker','bad-location')
            for c in configs:c['tasks']=[{'path':'tasks/bp-01-clean'}]
            with self.assertRaisesRegex(ValueError,'frozen'):
                isolate_protocol_tasks(root,configs,source)

    def test_missing_historical_zero_cannot_raise_passing_mean(self):
        from scripts.judge_check import audit
        read=Path.read_bytes
        def tampered(path):
            blob=read(path)
            if path==ROOT/'data/results.json':
                data=json.loads(blob)
                index=next(i for i,r in enumerate(data['runs']) if 'deepseek' in r['model'] and r['reward']==0)
                data['runs'].pop(index)
                return json.dumps(data).encode()
            return blob
        with patch.object(Path,'read_bytes',tampered): report=audit(ROOT)
        self.assertFalse(report['passed'])
        row=report['history']['core']['models']['verda/deepseek-4-1-flash-1017']
        self.assertIsNone(row['mean_reward'])

    def test_duplicate_missing_model_and_pending_history_fail(self):
        from scripts.judge_check import audit
        read=Path.read_bytes
        for mode in ('duplicate','duplicate-id','missing-model','pending'):
            def tampered(path):
                blob=read(path)
                if path==ROOT/'data/results.json':
                    data=json.loads(blob)
                    if mode=='duplicate': data['runs'][1]=data['runs'][0]
                    elif mode=='duplicate-id': data['runs'][1]['id']=data['runs'][0]['id']
                    elif mode=='missing-model': data['runs']=[r for r in data['runs'] if r['model']!='nop']
                    else: data['runs'][0]['status']='pending'
                    return json.dumps(data).encode()
                return blob
            with self.subTest(mode=mode),patch.object(Path,'read_bytes',tampered):
                self.assertFalse(audit(ROOT)['passed'])

    def test_offline_controls_cover_all_tasks_and_preserve_results(self):
        from scripts.judge_check import audit
        paths = [ROOT/'data/results.json', ROOT/'science_demo/results.json']
        before = [p.read_bytes() for p in paths]
        report = audit(ROOT)
        self.assertTrue(report['passed'])
        self.assertEqual(len(report['controls']), 40)
        for row in report['controls']:
            self.assertEqual(row['reference'], 1)
            self.assertEqual(row['noop'], 0)
            self.assertAlmostEqual(row['stop_early'], .1)
            self.assertEqual(row['confident_wrong'], 0)
            self.assertEqual(row['duplicate_keys'], 0)
            self.assertEqual(row['overflow_number'], 0)
        self.assertFalse(report['independent_repeats_completed'])
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_reference_uses_input_only_and_generalizes_parameters(self):
        from blueprint_gym.judge_agents import SCIENCE_REFERENCE
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d)/'input.json', Path(d)/'answer.json'
            # No gold or project imports are available to this isolated command.
            cases=[('0.07','-0.4','1.7',49/12482),('0.1','0','0',.005)]
            for task in sorted((ROOT/'science_demo/tasks').glob('science-a-*')):
                params=json.loads((task/'environment/input.json').read_text())
                cases.append((params['g'],params['c'],params['A'],json.loads((task/'tests/gold.json').read_text())['value']))
            for g,c,a,expected in cases:
                inp.write_text(json.dumps({'g':g,'c':c,'A':a}))
                subprocess.run([sys.executable,'-I','-c',SCIENCE_REFERENCE,str(inp),str(out)],check=True,cwd=d)
                self.assertAlmostEqual(json.loads(out.read_text())['value'],expected)

    def test_protocol_is_three_attempts_and_distinct_controls(self):
        from scripts.judge_protocol import build_configs
        configs = build_configs(ROOT, 'science', 'kimi', 'docker', 'review-example')
        self.assertEqual(len(configs),4)
        self.assertEqual(len({c['job_name'] for c in configs}),4)
        agent = next(c for c in configs if c['job_name'].endswith('-agent'))
        self.assertEqual(agent['n_attempts'],3)
        self.assertEqual(len(agent['tasks']),4)
        for c in configs:
            self.assertEqual(c['n_concurrent_trials'],1)
            self.assertEqual(c['environment']['type'],'docker')
        self.assertIn('CaseAReferenceAgent', configs[0]['agents'][0]['import_path'])
        self.assertIn('StopEarlyAgent', configs[-1]['agents'][0]['import_path'])

    def test_generation_needs_no_credentials_or_harbor_process(self):
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (ROOT/'science_demo/tasks').rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory() as d:
            run = subprocess.run([sys.executable,str(ROOT/'scripts/judge_protocol.py'),
                '--suite','science','--output',d,'--run-id','test-only'],cwd=ROOT,
                capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('NOT EXECUTED',run.stdout)
            self.assertEqual(len(list(Path(d).glob('*.json'))),5)
            protocol=json.loads((Path(d)/'protocol.json').read_text())
            self.assertEqual(protocol['task_snapshot']['network_policy'],
                             {'network_mode':'allowlist','allowed_hosts':['inference.verda.com']})
            self.assertFalse(protocol['task_snapshot']['runtime_egress_verified'])
            from harbor.models.job.config import JobConfig
            from harbor.models.task.config import TaskConfig
            for config_path in Path(d).glob('test-only-science-*.json'):
                config=json.loads(config_path.read_text())
                JobConfig.model_validate(config)
                for entry in config['tasks']:
                    copied=Path(entry['path'])
                    self.assertTrue(copied.is_relative_to(Path(d)))
                    parsed=TaskConfig.model_validate_toml((copied/'task.toml').read_text())
                    self.assertEqual(parsed.environment.network_mode.value,'allowlist')
                    self.assertEqual(parsed.environment.allowed_hosts,['inference.verda.com'])
                    self.assertEqual(parsed.verifier.environment.network_mode.value,'no-network')
                    original=ROOT/'science_demo/tasks'/copied.name
                    a=tomllib.loads((original/'task.toml').read_text())
                    b=tomllib.loads((copied/'task.toml').read_text())
                    b['environment']['network_mode']='public'
                    del b['environment']['allowed_hosts']
                    self.assertEqual(a,b)
                    for source in original.rglob('*'):
                        if source.is_file() and source.name!='task.toml':
                            self.assertEqual(source.read_bytes(),(copied/source.relative_to(original)).read_bytes())
            snapshot=protocol['task_snapshot']
            for row in snapshot['tasks']:
                for relative,hashes in row['files'].items():
                    self.assertEqual(hashes['source_sha256'],hashlib.sha256((ROOT/row['source']/relative).read_bytes()).hexdigest())
                    self.assertEqual(hashes['derived_sha256'],hashlib.sha256((Path(row['derived'])/relative).read_bytes()).hexdigest())
            again = subprocess.run([sys.executable,str(ROOT/'scripts/judge_protocol.py'),
                '--suite','science','--output',d,'--run-id','test-only'],cwd=ROOT,
                capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)
        self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (ROOT/'science_demo/tasks').rglob('*') if p.is_file()})


if __name__ == '__main__': unittest.main()
