"""Reproduce the private toy evidence locally, with one FFT job at a time."""
import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
from time import perf_counter

from .toy import estimate_diagonal, reference_limit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('validation.json'))
    args = parser.parse_args()
    # Set before NumPy's lazy import in estimate_diagonal.
    for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    started = perf_counter()
    parameter_path = Path(__file__).with_name('parameters.json')
    parameter_bytes = parameter_path.read_bytes()
    cases = []
    for row in json.loads(parameter_bytes):
        params = {key: row[key] for key in ('g', 'c', 'A')}
        reference = reference_limit(**params)
        g, c = Fraction(params['g']), Fraction(params['c'])
        historical = g * g / (2 * (1 - g * c)**2)
        coarse = estimate_diagonal(**params, grid_size=512)
        fine = estimate_diagonal(**params, grid_size=1024)
        change = [a / b - 1 for a, b in zip(coarse['ratios'], fine['ratios'])]
        cases.append({
            'id': row['id'], 'parameters': params,
            'reference': {'numerator': reference.numerator, 'denominator': reference.denominator,
                          'value': float(reference)},
            'historical_wrong': float(historical),
            'historical_relative_error': float(historical / reference - 1),
            'control_nondiscriminating': params['A'] == '0',
            **fine,
            'finite_index_relative_span': (max(fine['ratios']) - min(fine['ratios'])) / float(reference),
            'grid_sensitivity': {
                'compared_grid_size': coarse['grid_size'], 'compared_radius': coarse['radius'],
                'compared_ratios': coarse['ratios'], 'relative_changes': change,
                'max_relative_change': max(map(abs, change)), 'runtime_sec': coarse['runtime_sec'],
            },
        })
    passed = all(max(map(abs, case['relative_errors'])) < 1e-3
                 and case['grid_sensitivity']['max_relative_change'] < 1e-3 for case in cases)
    import numpy as np
    report = {
        'status': 'validated_private_candidate' if passed else 'numerical_validation_failed',
        'definition': {
            'f': 'A + (1-u)^(3/2)', 'E': 'g*(c+f(u)+f(v))',
            'F': '-0.5*(log(1-E)+E)', 'a_ii': '[u^i v^i]F', 'C_i': '[u^i](1-u)^(3/2)',
            'target': 'lim(i->infinity) a_ii/C_i^2', 'branch': 'principal, analytic at u=v=0',
        },
        'method': {
            'coefficient_extraction': 'FFT2 of directly sampled F on |u|=|v|=exp(-4/M)',
            'normalization': 'M^-2 * radius^(-2*i), divided by binomial recurrence C_i^2',
            'independence': 'reference formula used only after numerical coefficient extraction',
            'target_relative_tolerance': 1e-3,
            'python_version': platform.python_version(), 'numpy_version': np.__version__,
            'thread_environment': {key: os.environ[key] for key in
                                   ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')},
        },
        'parameters_sha256': hashlib.sha256(parameter_bytes).hexdigest(),
        'cases': cases, 'runtime_sec': perf_counter() - started,
        'limitations': [
            'Owner approval recorded 2026-11-15 covers the generic mathematical toy demonstration/publication, independently rewritten code, numerical outputs, and validation using Verda or Modal. This copy remains owner-private; original scientific projects, research posts and identities, unpublished material models and research datasets, and raw scientific-server files and logs are excluded.',
            'Independent toy derivation and computation; original research code, logs, and lattice results were not inspected or rerun.',
            'Finite-index and grid agreement is empirical, not a certified numerical error enclosure or proof of the limit.',
            'roundoff_ratio_scale_not_bound is an epsilon-based diagnostic, not a rigorous bound.',
            'Grid comparisons change both M and radius; they measure combined aliasing/roundoff sensitivity.',
            'A=0 is nondiscriminating: the historical expression equals the correct reference.',
            'Higher indices eventually amplify double-precision error; only reported indices are validated.',
            'The conservative sufficient analytic domain condition is required; no claim covers parameters outside it.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(f'{report["status"]}: {len(cases)} cases, {report["runtime_sec"]:.3f}s; {args.output}')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
