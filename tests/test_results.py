import unittest
from scripts.export_results import summarize

class ResultsTest(unittest.TestCase):
    def test_failures_remain_in_expected_denominator_and_cost_unknown(self):
        runs = [dict(model='m', family='area', condition='scan', status='completed', reward=1.0, cost_usd=0.2),
                dict(model='m', family='area', condition='scan', status='failed', reward=None, cost_usd=None)]
        row = summarize(runs)[0]
        self.assertEqual(row['n'], 2)
        self.assertEqual(row['completed'], 1)
        self.assertEqual(row['failed'], 1)
        self.assertEqual(row['mean_reward'], 0.5)
        self.assertIsNone(row['cost_usd'])
    def test_no_synthetic_success_for_missing_reward(self):
        row = summarize([dict(model='m', family='area', condition='vector', status='failed', reward=None, cost_usd=None)])[0]
        self.assertEqual(row['mean_reward'], 0)
        self.assertEqual(row['completed'], 0)

    def test_scrubber_removes_secret_values_and_named_credentials(self):
        from scripts.export_results import scrub
        result = scrub({'message': 'Bearer abc123xx and private-value', 'apiKey': 'xyz', 'steps': ['private-value']}, ['private-value'])
        self.assertNotIn('private-value', str(result))
        self.assertNotIn('abc123xx', str(result))
        self.assertEqual(result['apiKey'], '[REDACTED]')

    def test_valid_reward_with_exception_is_visible_and_graded(self):
        from scripts.export_results import classify
        status = classify(True, 'NonZeroAgentExitCodeError', True)
        self.assertEqual(status, 'graded_with_warning')
        row = summarize([dict(model='m', family='area', condition='scan', status=status, reward=.8, cost_usd=None)])[0]
        self.assertEqual((row['mean_reward'], row['completed'], row['failed'], row['warnings']), (.8, 1, 0, 1))

    def test_unstarted_trials_stay_in_denominator(self):
        rows = [dict(model='m', family='area', condition='scan', status='pending', reward=None, cost_usd=None) for _ in range(36)]
        row = summarize(rows)[0]
        self.assertEqual((row['n'], row['pending'], row['failed'], row['mean_reward']), (36, 36, 0, None))

    def test_numeric_usage_counts_survive_scrubbing(self):
        from scripts.export_results import scrub
        obj = {'n_input_tokens': 123, 'n_output_tokens': 45, 'api_key': 'abc', 'access_token': 'def'}
        self.assertEqual(scrub(obj, []), {'n_input_tokens': 123, 'n_output_tokens': 45, 'api_key': '[REDACTED]', 'access_token': '[REDACTED]'})

class ReplayBundleTest(unittest.TestCase):
    def test_bundle_contains_actual_artifacts_and_preserves_usage(self):
        import json, tempfile
        from pathlib import Path
        from scripts.export_results import replay_bundle
        with tempfile.TemporaryDirectory() as tmp:
            trial = Path(tmp)
            for folder in ('agent', 'artifacts/workspace', 'verifier'):
                (trial/folder).mkdir(parents=True)
            (trial/'agent/trajectory.json').write_text(json.dumps({'steps': [], 'n_input_tokens': 12, 'api_key': 'secret-value'}))
            (trial/'artifacts/workspace/answer.json').write_text('{"value": 1.25, "confidence": 0.712345}')
            (trial/'verifier/breakdown.json').write_text('{"total": 0.95}')
            bundle = replay_bundle(trial, {'id': 'actual', 'reward': .95}, ['secret-value'])
            self.assertEqual(bundle['format'], 'blueprint-replay-v1')
            self.assertEqual(bundle['trajectory']['n_input_tokens'], 12)
            self.assertEqual(bundle['trajectory']['api_key'], '[REDACTED]')
            self.assertEqual(bundle['submission']['confidence'], .712345)
            self.assertEqual(bundle['score']['total'], .95)
            self.assertIsNone(bundle['submission_error'])

    def test_missing_malformed_and_oversized_submissions_are_safe(self):
        import tempfile
        from pathlib import Path
        from scripts.export_results import replay_bundle
        with tempfile.TemporaryDirectory() as tmp:
            trial = Path(tmp)
            (trial/'agent').mkdir()
            (trial/'agent/trajectory.json').write_text('{}')
            (trial/'artifacts/workspace').mkdir(parents=True)
            path = trial/'artifacts/workspace/answer.json'
            self.assertEqual(replay_bundle(trial, {}, [])['submission_error'], 'Submission missing')
            path.write_text('{"value": NaN}')
            self.assertEqual(replay_bundle(trial, {}, [])['submission_error'], 'Submission invalid JSON')
            path.write_bytes(b' ' * (1024 * 1024 + 1))
            self.assertEqual(replay_bundle(trial, {}, [])['submission_error'], 'Submission too large')

class ExportCompletionTest(unittest.TestCase):
    def test_default_export_does_not_search_for_credential_files(self):
        from unittest.mock import patch
        with patch('dotenv.dotenv_values', side_effect=AssertionError('unexpected credential file read')):
            self.export_fixture({})

    def test_invalid_jobs_cannot_replace_captured_results(self):
        from unittest.mock import patch
        import scripts.export_results as exporter
        for jobs in ([], ['../outside'], ['/absolute']):
            with self.subTest(jobs=jobs), patch.object(exporter, 'publish_json') as publish:
                with self.assertRaises(ValueError):
                    exporter.export(jobs)
                publish.assert_not_called()

    def export_fixture(self, trials, job_finished=False):
        import json, tempfile
        from pathlib import Path
        from unittest.mock import patch
        import scripts.export_results as exporter
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'data').mkdir()
            (root/'data/catalog.json').write_text(json.dumps([
                {'id': name, 'family': 'area', 'condition': 'vector'} for name in trials]))
            job = root/'runs/raw/job'
            job.mkdir(parents=True)
            (job/'config.json').write_text(json.dumps({'agents': [{'name': 'nop'}],
                'tasks': [{'path': f'tasks/{name}'} for name in trials]}))
            if job_finished:
                (job/'result.json').write_text('{"finished_at": "2026-01-01T00:00:00Z"}')
            for name, result in trials.items():
                if result is not None:
                    (job/name).mkdir()
                    (job/name/'result.json').write_text(json.dumps(dict(task_name=name, **result)))
            with patch.object(exporter, 'ROOT', root):
                exporter.export(['job'])
            return json.loads((root/'data/results.json').read_text())

    def test_finished_warning_export_is_complete_and_preserves_zero_reward(self):
        payload = self.export_fixture({
            'clean': {'verifier_result': {'rewards': {'reward': .8}}, 'agent_result': {'cost_usd': .2}},
            'warning': {'verifier_result': {'rewards': {'reward': 0}}, 'reward_valid': True,
                        'exception_info': {'exception_type': 'AgentTimeoutError'}}}, job_finished=True)
        self.assertEqual(payload['status'], 'complete')
        self.assertIn('finished', payload['message'])
        clean, warning = payload['runs']
        self.assertEqual((clean['status'], clean['reward'], clean['cost_usd']), ('completed', .8, .2))
        self.assertEqual((warning['status'], warning['reward'], warning['error_type']),
                         ('graded_with_warning', 0, 'AgentTimeoutError'))
        row = payload['summary'][0]
        self.assertEqual((row['n'], row['completed'], row['warnings'], row['failed'], row['pending'], row['mean_reward']),
                         (2, 2, 1, 0, 0, .4))
        self.assertIsNone(row['cost_usd'])

    def test_finished_failed_and_missing_export_is_complete_with_all_rows(self):
        payload = self.export_fixture({
            'failed': {'exception_info': {'exception_type': 'VerifierTimeoutError'},
                       'verifier_result': {'rewards': {'reward': .9}}, 'reward_valid': False},
            'missing': None}, job_finished=True)
        self.assertEqual(payload['status'], 'complete')
        self.assertIn('finished', payload['message'])
        self.assertEqual([(r['task_id'], r['status'], r['reward'], r['error_type']) for r in payload['runs']],
                         [('failed', 'failed', None, 'VerifierTimeoutError'), ('missing', 'missing', None, None)])
        row = payload['summary'][0]
        self.assertEqual((row['n'], row['completed'], row['failed'], row['pending'], row['mean_reward']),
                         (2, 0, 2, 0, 0))

    def test_pending_export_remains_partial_with_unavailable_mean(self):
        payload = self.export_fixture({'clean': {'verifier_result': {'rewards': {'reward': 1}}}, 'pending': None})
        self.assertEqual(payload['status'], 'partial')
        self.assertIn('pending', payload['message'])
        self.assertNotIn('All exported trials are finished', payload['message'])
        self.assertEqual((len(payload['runs']), payload['summary'][0]['pending']), (2, 1))
        self.assertIsNone(payload['summary'][0]['mean_reward'])

    def test_empty_export_remains_partial(self):
        payload = self.export_fixture({})
        self.assertEqual(payload['status'], 'partial')
        self.assertNotIn('All exported trials are finished', payload['message'])
        self.assertEqual((payload['runs'], payload['summary']), ([], []))


class ExportSafetyTest(unittest.TestCase):
    def test_overflowing_submission_does_not_stop_export(self):
        import json, tempfile
        from pathlib import Path
        from unittest.mock import patch
        import scripts.export_results as exporter
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'data').mkdir()
            (root/'data/catalog.json').write_text(json.dumps([
                {'id': name, 'family': 'area', 'condition': 'vector'} for name in ('a', 'b')]))
            job = root/'runs/raw/job'
            job.mkdir(parents=True)
            (job/'config.json').write_text(json.dumps({'agents': [{'name': 'nop'}],
                'tasks': [{'path': 'tasks/a'}, {'path': 'tasks/b'}]}))
            for name, answer in [('a', '{"confidence": 1e999}'), ('b', '{"value": 2}')]:
                trial = job/name
                for folder in ('agent', 'artifacts/workspace'):
                    (trial/folder).mkdir(parents=True)
                (trial/'result.json').write_text(json.dumps({'task_name': name, 'verifier_result': {'rewards': {'reward': 1}}}))
                (trial/'agent/trajectory.json').write_text('{"steps": []}')
                (trial/'artifacts/workspace/answer.json').write_text(answer)
            with patch.object(exporter, 'ROOT', root):
                exporter.export(['job'])
            bad = json.loads((root/'data/trajectories/job-a.json').read_text())
            good = json.loads((root/'data/trajectories/job-b.json').read_text())
            self.assertIsNone(bad['submission'])
            self.assertEqual(bad['submission_error'], 'Submission invalid JSON')
            self.assertEqual(good['submission'], {'value': 2})
            self.assertEqual(len(json.loads((root/'data/results.json').read_text())['runs']), 2)

    def test_environment_only_secret_is_scrubbed_and_blocks_publication(self):
        import json, tempfile
        from pathlib import Path
        from unittest.mock import patch
        import scripts.export_results as exporter
        sentinel = 'fixture-environment-only-credential'
        dotenv_sentinel = 'fixture-dotenv-only-credential'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'data').mkdir()
            (root/'data/catalog.json').write_text(json.dumps([{'id': 'a', 'family': 'area', 'condition': 'vector'}]))
            job = root/'runs/raw/job'
            trial = job/'a'
            (trial/'agent').mkdir(parents=True)
            (job/'config.json').write_text(json.dumps({'agents': [{'name': 'opencode', 'model_name': 'model'}], 'tasks': [{'path': 'tasks/a'}]}))
            (trial/'result.json').write_text(json.dumps({'task_name': 'a', 'verifier_result': {'rewards': {'reward': 1}}, 'agent_result': {'cost_usd': .2}}))
            (trial/'agent/trajectory.json').write_text(json.dumps({'steps': [{'observation': {'text': sentinel, 'other': dotenv_sentinel}}], 'n_input_tokens': 42}))
            original_publish = exporter.publish_json
            def checked_publish(path, payload, secrets):
                with self.assertRaises(ValueError):
                    original_publish(root/'blocked.json', {'nested': [sentinel]}, secrets)
                return original_publish(path, payload, secrets)
            with patch.object(exporter, 'ROOT', root), patch('dotenv.dotenv_values', return_value={'OTHER_SECRET': dotenv_sentinel}) as read_explicit_file, patch.dict(exporter.os.environ, {'VERDA_INFERENCE_API_KEY': sentinel}, clear=True), patch.object(exporter, 'publish_json', side_effect=checked_publish):
                exporter.export(['job'], secrets_file=root/'redaction.env')
                read_explicit_file.assert_called_once_with(root/'redaction.env')
            bundle = json.loads((root/'data/trajectories/job-a.json').read_text())
            self.assertNotIn(sentinel, json.dumps(bundle))
            self.assertNotIn(dotenv_sentinel, json.dumps(bundle))
            self.assertEqual(bundle['trajectory']['steps'][0]['observation']['text'], '[REDACTED]')
            self.assertEqual(bundle['trajectory']['n_input_tokens'], 42)
            self.assertEqual(json.loads((root/'data/results.json').read_text())['runs'][0]['cost_usd'], .2)
            self.assertFalse((root/'blocked.json').exists())

    def test_atomic_publication_preserves_previous_file_on_failures(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.export_results import publish_json
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'result.json'
            target.write_text('{"previous": true}\n')
            for payload, secrets in [({'value': float('inf')}, []), ({'value': 'credential-value'}, ['credential-value'])]:
                with self.assertRaises(ValueError):
                    publish_json(target, payload, secrets)
                self.assertEqual(target.read_text(), '{"previous": true}\n')
            import tempfile as temporary_files
            real_temporary_file = temporary_files.NamedTemporaryFile
            def broken_tempfile(*args, **kwargs):
                file = real_temporary_file(*args, **kwargs)
                file.write = lambda _text: (_ for _ in ()).throw(OSError('write failed'))
                return file
            with patch('scripts.export_results.tempfile.NamedTemporaryFile', side_effect=broken_tempfile):
                with self.assertRaises(OSError):
                    publish_json(target, {'next': True}, [])
            self.assertEqual(target.read_text(), '{"previous": true}\n')
            self.assertEqual(list(Path(tmp).iterdir()), [target])
            with patch('scripts.export_results.os.replace', side_effect=OSError('replace failed')):
                with self.assertRaises(OSError):
                    publish_json(target, {'next': True}, [])
            self.assertEqual(target.read_text(), '{"previous": true}\n')
            self.assertEqual(list(Path(tmp).iterdir()), [target])
            publish_json(target, {'next': True}, [])
            self.assertEqual(target.read_text(), '{\n  "next": true\n}\n')
