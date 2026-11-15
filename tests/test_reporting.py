"""Reporting contracts: fixtures stay temporary and never enter public exports."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from scripts import render_results as reporting
except ImportError:
    reporting = None


def run(task='t', status='completed', reward=1.0, **extra):
    return dict(id=f'full-deepseek-{task}', task_id=task,
                model='verda/deepseek-4-1-flash-1017', agent='opencode',
                family='area', condition='vector', status=status, reward=reward,
                cost_usd=None, duration_sec=12, error_type=None,
                trajectory_url=f'/api/runs/full-deepseek-{task}', **extra)


def bundle(record, value_score=1, valid=True):
    return dict(format='blueprint-replay-v1', run={k: record[k] for k in
                ('id', 'task_id', 'model', 'status', 'reward', 'error_type', 'duration_sec', 'cost_usd')},
                trajectory={'steps': []}, submission={'value': 7, 'unit': 'm2', 'confidence': .712345},
                score={'valid': valid, 'value_score': value_score, 'reward': .9,
                       'components': {'value': .75, 'evidence': .05, 'calibration': .1}},
                submission_error=None)


def planned_fixture():
    catalog = [{'id': f't{i}', 'family': 'area', 'condition': 'vector'} for i in range(36)]
    rows = []
    for job, model in reporting.PLANNED:
        for task in catalog:
            row = run(task['id'], 'pending', None)
            row.update(id=f'{job}-{task["id"]}', model=model, trajectory_url=None)
            rows.append(row)
    return {'status': 'partial', 'scope': 'evaluation', 'runs': rows}, catalog


class ReportingTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(reporting, 'The reproducible report generator is missing')

    def test_incomplete_group_has_no_mean_and_cost_stays_unknown(self):
        rows = [run('a'), run('b', 'pending', None)]
        result = reporting.aggregate(rows)
        self.assertEqual((result['n'], result['completed'], result['pending']), (2, 1, 1))
        self.assertIsNone(result['mean_reward'])
        self.assertIsNone(result['cost_usd'])

    def test_finished_failure_counts_zero_even_with_score_reward(self):
        rows = [run('a', reward=.8), run('b', 'failed', None)]
        self.assertEqual(reporting.aggregate(rows)['mean_reward'], .4)
        self.assertEqual(reporting.aggregate(rows)['failed'], 1)

    def test_warning_is_graded_and_not_a_clean_completion(self):
        row = run(status='graded_with_warning', reward=.8)
        row['error_type'] = 'NonZeroAgentExitCodeError'
        result = reporting.aggregate([row])
        self.assertEqual((result['completed'], result['warnings'], result['failed']), (1, 1, 0))
        self.assertEqual(result['mean_reward'], .8)

    def test_examples_require_actual_record_bundle_and_model(self):
        good = run('a'); bad = run('b'); trap = run('c')
        oracle = run('d'); oracle['agent'] = 'oracle'
        rows = [good, bad, trap, oracle]
        catalog = [{'id': r['task_id'], 'question': 'Measured room?', 'trap': r is trap} for r in rows]
        bundles = {r['id']: bundle(r, 0 if r is bad else 1) for r in rows}
        selected = reporting.select_examples(rows, catalog, bundles)
        self.assertEqual([selected[k]['run']['task_id'] for k in ('success', 'failure', 'trap')], ['a', 'b', 'c'])
        self.assertEqual(selected['trap']['outcome'], 'Trap quantity succeeded; no misread is established.')
        self.assertEqual(selected['success']['submission']['confidence'], .712345)
        self.assertIsNone(reporting.select_examples(rows, catalog, {})['success'])

    def test_oracle_named_model_never_becomes_a_model_example(self):
        row = run('a'); row['model'] = 'oracle'
        self.assertIsNone(reporting.select_examples([row], [{'id': 'a'}], {row['id']: bundle(row)})['success'])

    def test_invalid_submission_is_failure_but_transport_error_is_not_numeric_miss(self):
        failed = run('a', 'failed', None)
        artifact = bundle(failed); artifact.update(submission=None, score=None, submission_error='Submission invalid JSON')
        selected = reporting.select_examples([failed], [{'id': 'a', 'question': 'Q', 'trap': True}], {failed['id']: artifact})
        self.assertEqual(selected['failure']['run']['reward'], None)
        self.assertIn('invalid', selected['failure']['outcome'])
        self.assertNotIn('misread', selected['trap']['outcome'].lower().replace('no misread', ''))
        artifact.update(submission_error=None)
        self.assertIsNone(reporting.select_examples([failed], [{'id': 'a', 'trap': False}], {failed['id']: artifact})['failure'])

    def test_missing_infrastructure_artifact_does_not_establish_invalid_answer(self):
        failed = run('a', 'failed', None)
        failed['error_type'] = 'InfrastructureError'
        artifact = bundle(failed)
        artifact.update(submission=None, score=None, submission_error='Submission missing')
        catalog = [{'id': 'a', 'trap': True}]
        selected = reporting.select_examples([failed], catalog, {failed['id']: artifact})
        self.assertIsNone(selected['failure'])
        self.assertIn('unavailable', selected['trap']['outcome'])
        self.assertNotIn('invalid', selected['trap']['outcome'])
        # Evidence classification must not alter the official failed row/denominator.
        self.assertEqual(failed['status'], 'failed')
        self.assertEqual(reporting.aggregate([failed])['mean_reward'], 0)

        miss = run('b')
        selected = reporting.select_examples([failed, miss], catalog + [{'id': 'b'}],
                                             {failed['id']: artifact, miss['id']: bundle(miss, 0)})
        self.assertEqual(selected['failure']['run']['id'], miss['id'])

    def test_only_explicit_artifact_parse_errors_establish_invalidity(self):
        row = run('a', 'failed', None)
        for error, invalid in [('Submission invalid JSON', True), ('Submission too large', True),
                               ('Submission missing', False), ('Submission unavailable', False)]:
            artifact = bundle(row)
            artifact.update(submission=None, score=None, submission_error=error)
            with self.subTest(error=error):
                selected = reporting.select_examples([row], [{'id': 'a'}], {row['id']: artifact})
                self.assertEqual(selected['failure'] is not None, invalid)

    def test_unlisted_or_mismatched_replay_cannot_supply_example(self):
        row = run('a'); data = bundle(row)
        row['trajectory_url'] = None
        self.assertIsNone(reporting.select_examples([row], [{'id': 'a'}], {row['id']: data})['success'])
        row['trajectory_url'] = f'/api/runs/{row["id"]}'
        data['run']['reward'] = .01
        with self.assertRaises(ValueError):
            reporting.select_examples([row], [{'id': 'a'}], {row['id']: data})

    def test_saved_json_array_can_be_a_real_invalid_submission_example(self):
        row = run('a', reward=0)
        data = bundle(row, 0, valid=False)
        data['submission'] = ['invalid saved submission']
        selected = reporting.select_examples([row], [{'id': 'a'}], {row['id']: data})
        self.assertIsNotNone(selected['failure'])
        self.assertIn('invalid', selected['failure']['outcome'])
        self.assertIsNone(selected['failure']['submission'])

    def test_malformed_score_array_aborts_instead_of_becoming_missing(self):
        row = run('a'); data = bundle(row); data['score'] = []
        with self.assertRaises(ValueError):
            reporting.select_examples([row], [{'id': 'a'}], {row['id']: data})

    def test_partial_report_preserves_official_missing_reward_and_pending_examples(self):
        row = run('a', 'failed', None)
        text = reporting.render_report({'status': 'partial', 'scope': 'evaluation', 'runs': [row]},
            [{'id': 'a', 'family': 'area', 'condition': 'vector', 'question': 'Q'}],
            {row['id']: bundle(row, 0)}, {}, {'data/results.json': 'abc'}, '2026-01-01T00:00:00Z')
        self.assertIn('Official reward: unavailable', text)
        self.assertIn('Pending: no qualifying recorded', text)
        self.assertIn('unavailable (`null`)', text)
        self.assertNotIn('Official reward: 0.900000', text)

    def test_diagnostics_use_recorded_timestamps_and_keep_failed_official_reward_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); job = root/'runs/raw/smoke-no-snapshot'
            trial = job/'t'; trial.mkdir(parents=True)
            (trial/'result.json').write_text(json.dumps({'task_name': 'bp-10-vector',
                'started_at': '2026-01-01T00:00:00Z', 'finished_at': '2026-01-01T00:00:09Z',
                'verifier_result': {'rewards': {'reward': .8}}, 'reward_valid': False,
                'exception_info': {'exception_type': 'VerifierTimeoutError'}}))
            diagnostics = reporting.load_diagnostics(root, {})
            row = diagnostics['smoke-no-snapshot']['trials'][0]
            self.assertEqual(row['duration_sec'], 9)
            self.assertIsNone(row['reward'])
            self.assertEqual(row['status'], 'failed')

    def test_invalid_input_cannot_destroy_old_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'data').mkdir()
            (root/'data/catalog.json').write_text(json.dumps(planned_fixture()[1]))
            target = root/'RESULTS.md'; target.write_text('previous report\n')
            for content in ('{', '{"runs": [], "runs": []}', '{"runs": [NaN]}', '{"runs": []}'):
                (root/'data/results.json').write_text(content)
                with self.assertRaises(ValueError):
                    reporting.update_report(root, observed_at='fixed')
                self.assertEqual(target.read_text(), 'previous report\n')

    def test_atomic_replace_failure_preserves_report_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'data').mkdir()
            payload, catalog = planned_fixture()
            for name, data in [('results', payload), ('catalog', catalog)]:
                (root/f'data/{name}.json').write_text(json.dumps(data))
            target = root/'RESULTS.md'; target.write_text('previous report\n')
            with patch('scripts.render_results.os.replace', side_effect=OSError('replace failed')):
                with self.assertRaises(OSError):
                    reporting.update_report(root, observed_at='fixed')
            self.assertEqual(target.read_text(), 'previous report\n')
            self.assertEqual(list(root.glob('.RESULTS.md.*.tmp')), [])
            reporting.update_report(root, observed_at='2026-01-01T00:00:00Z')
            actual = target.read_text()
            self.assertIn('0/144 graded', actual)
            self.assertIn('144 pending', actual)
            self.assertTrue(reporting.update_report(root, check=True, observed_at='later'))
            self.assertEqual(target.read_text(), actual)

    def test_check_ignores_only_observation_time_and_never_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); target = root/'RESULTS.md'
            old = '# Results\n\nObserved at: `earlier`.\nMean reward: unavailable\n'
            target.write_text(old)
            fresh = old.replace('earlier', 'later')
            self.assertTrue(reporting.check_report(target, fresh))
            self.assertFalse(reporting.check_report(target, fresh.replace('unavailable', '1.000000')))
            self.assertEqual(target.read_text(), old)

    def test_planned_validation_rejects_old_oracle_missing_rows_and_false_completion(self):
        payload, catalog = planned_fixture()
        reporting.validate_matrix(payload, catalog)
        for mutate in ('old_oracle', 'missing', 'false_complete'):
            bad = copy.deepcopy(payload)
            if mutate == 'old_oracle': bad['runs'][0]['id'] = 'full-oracle-t0'
            elif mutate == 'missing': bad['runs'].pop()
            else: bad['status'] = 'complete'
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                reporting.validate_matrix(bad, catalog)

    def test_complete_matrix_accepts_terminal_warnings_failed_and_missing_rows(self):
        payload, catalog = planned_fixture()
        payload['status'] = 'complete'
        for row in payload['runs']:
            row.update(status='completed', reward=1)
        payload['runs'][0].update(status='graded_with_warning', reward=0, error_type='AgentTimeoutError')
        payload['runs'][1].update(status='failed', reward=None, error_type='VerifierTimeoutError')
        payload['runs'][2].update(status='missing', reward=None, trajectory_url=None)
        reporting.validate_matrix(payload, catalog)

    def test_unsafe_task_id_cannot_select_a_file_outside_replay_directory(self):
        payload, catalog = planned_fixture()
        catalog[0]['id'] = '../t0'
        for row in payload['runs']:
            if row['task_id'] == 't0':
                row['task_id'] = '../t0'
                row['id'] = row['id'].replace('-t0', '-../t0')
        with self.assertRaises(ValueError):
            reporting.validate_matrix(payload, catalog)
