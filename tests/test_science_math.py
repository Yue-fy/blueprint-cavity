"""Independent checks for the private Case A toy (no research-source access)."""
from fractions import Fraction
import importlib
import importlib.util
import json

import pytest


def toy():
    assert importlib.util.find_spec('science_demo.toy') is not None, 'scientific toy API is missing'
    return importlib.import_module('science_demo.toy')


@pytest.mark.parametrize('g,c,A,expected', [
    ('0.1', '0.5', '1', Fraction(2, 225)),
    ('0.1', '0.5', '0', Fraction(2, 361)),
    ('0.07', '-0.4', '1.7', Fraction(49, 12482)),
    ('-0.11', '0.9', '0.6', Fraction(6050, 1515361)),
])
def test_full_boundary_value_exact_reference(g, c, A, expected):
    # Omitting 2A or losing the square must fail, for either sign of g.
    assert toy().reference_limit(g, c, A) == expected


def test_fraction_inputs_and_nondiscriminating_control():
    assert toy().reference_limit(Fraction(1, 10), Fraction(1, 2), 0) == Fraction(2, 361)


@pytest.mark.parametrize('g,c,A', [('1', '0', '0'), ('0.1', '10', '0')])
def test_unsafe_analytic_domain_rejected(g, c, A):
    with pytest.raises(ValueError, match='domain'):
        toy().reference_limit(g, c, A)
    with pytest.raises(ValueError, match='domain'):
        toy().estimate_diagonal(g, c, A, grid_size=64, indices=(1,))


def test_fft_low_coefficients_are_not_the_asymptotic_answer():
    # F_uv(0,0) = (1/2) (g*(-3/2))**2 / (1-g*(c+2A+2))**2.
    # For these inputs a_11=9/242, C_1**2=9/4, so ratio=2/121.
    result = toy().estimate_diagonal('0.1', '0.5', '1', grid_size=256, indices=(1, 2))
    assert result['coefficients'][0] == pytest.approx(9 / 242, rel=2e-5)
    assert result['ratios'][0] == pytest.approx(2 / 121, rel=2e-5)
    assert abs(result['ratios'][0] - 2 / 225) > 0.005
    assert result['method'] == 'direct_function_fft2'


@pytest.mark.parametrize('g,c,A', [('0.1', '0.5', '1'), ('-0.11', '0.9', '0.6')])
def test_fft_limit_and_grid_sensitivity(g, c, A):
    coarse = toy().estimate_diagonal(g, c, A, grid_size=512, indices=(80, 100, 120))
    fine = toy().estimate_diagonal(g, c, A, grid_size=1024, indices=(80, 100, 120))
    assert max(abs(x) for x in fine['relative_errors']) < 1e-3
    assert max(abs(a / b - 1) for a, b in zip(coarse['ratios'], fine['ratios'])) < 1e-3
    assert fine['runtime_sec'] > 0
    assert 0 < fine['radius'] < 1
    assert fine['domain_bound'] < 1
    assert fine['max_imaginary_ratio'] < 1e-3


def test_zero_coupling_has_zero_coefficients_without_nan():
    result = toy().estimate_diagonal('0', '0.5', '1', grid_size=64, indices=(4, 8))
    assert result['ratios'] == [0.0, 0.0]
    assert result['relative_errors'] == [0.0, 0.0]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('grid,indices', [(31, (1,)), (64, (0,)), (64, (64,)), (64, ())])
def test_invalid_sampling_request_is_rejected(grid, indices):
    with pytest.raises(ValueError):
        toy().estimate_diagonal('0.1', '0.5', '1', grid_size=grid, indices=indices)


def test_validation_cli_writes_actual_four_case_evidence(tmp_path):
    # A missing validator or formula-only report cannot produce observed FFT metadata.
    assert importlib.util.find_spec('science_demo.validate') is not None, 'validation CLI is missing'
    import subprocess
    import sys
    destination = tmp_path / 'validation.json'
    subprocess.run([sys.executable, '-m', 'science_demo.validate', '--output', str(destination)], check=True)
    report = json.loads(destination.read_text())
    assert report['status'] == 'validated_private_candidate'
    assert {c['id'] for c in report['cases']} == {'a-01', 'a-02', 'a-03', 'a-04'}
    assert report['parameters_sha256']
    for case in report['cases']:
        assert max(map(abs, case['relative_errors'])) < 1e-3
        assert case['grid_sensitivity']['compared_grid_size'] == 512
        assert case['grid_sensitivity']['max_relative_change'] < 1e-3
        assert case['runtime_sec'] > 0
        assert len(case['coefficients']) == len(case['indices']) == 3
    json.dumps(report, allow_nan=False)


def test_domain_decision_uses_exact_rationals_near_boundary():
    # At g=1/8,A=0 the exact c threshold is 8-4*sqrt(2).
    # Both decimal bounds round to 1.0 in binary64; only the first is safe.
    assert toy().reference_limit('0.125', '2.343145750507619804793245103', '0') > 0
    with pytest.raises(ValueError, match='domain'):
        toy().reference_limit('0.125', '2.343145750507619804793245104', '0')
