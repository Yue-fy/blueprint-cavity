"""Private Case A: exact limit and independent direct-function FFT coefficients.

The FFT coefficient path never substitutes the reference limit for a coefficient.
Use a single-thread process (OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1).
"""
from fractions import Fraction
import math
from time import perf_counter


def _parameters(g, c, A):
    values = tuple(Fraction(x) for x in (g, c, A))
    gq, cq, aq = values
    remainder = 1 - abs(gq) * (abs(cq) + 2 * abs(aq))
    # remainder > 4*sqrt(2)*|g|, tested without rounding sqrt(2).
    if remainder <= 0 or remainder * remainder <= 32 * gq * gq:
        raise ValueError('parameters fail the sufficient analytic domain bound < 1')
    bound = float(1 - remainder) + 4 * math.sqrt(2) * float(abs(gq))
    return values, bound


def reference_limit(g, c, A) -> Fraction:
    """Exact rational limit under the conservative no-extra-singularity condition."""
    (g, c, A), _ = _parameters(g, c, A)
    return g * g / (2 * (1 - g * (c + 2 * A))**2)


def estimate_diagonal(g, c, A, *, grid_size=1024, indices=(80, 100, 120)) -> dict:
    """Extract a_ii by a trapezoidal Cauchy integral/FFT2 of the defining F.

    Radius exp(-4/M) suppresses aliases by exp(-4) per wrapped index.
    This is a floating-point experiment, not a certified error enclosure.
    Grid <= 2048 deliberately bounds working memory for this private demo.
    """
    started = perf_counter()
    values, bound = _parameters(g, c, A)
    indices = tuple(indices)
    if (not isinstance(grid_size, int) or isinstance(grid_size, bool)
            or grid_size < 32 or grid_size > 2048
            or not indices or any(not isinstance(i, int) or isinstance(i, bool)
                                  or i < 1 or i >= grid_size for i in indices)):
        raise ValueError('use grid_size 32..2048 and integer indices 1..grid_size-1')
    import numpy as np

    gf, cf, af = map(float, values)
    radius = math.exp(-4 / grid_size)
    z = radius * np.exp(2j * np.pi * np.arange(grid_size) / grid_size)
    f = af + (1 - z)**1.5
    E = gf * (cf + f[:, None] + f[None, :])
    max_abs_E = float(np.max(np.abs(E)))
    F = -0.5 * (np.log1p(-E) + E)
    max_abs_F = float(np.max(np.abs(F)))
    del E
    transform = np.fft.fft2(F) / grid_size**2
    del F
    C = [1.0]
    for i in range(1, max(indices) + 1):
        C.append(C[-1] * (i - 2.5) / i)
    coefficients = [transform[i, i] / radius**(2 * i) for i in indices]
    ratios_complex = [a / C[i]**2 for a, i in zip(coefficients, indices)]
    ratios = [float(x.real) for x in ratios_complex]
    reference = float(reference_limit(*values))  # Diagnostic only, after extraction.
    errors = [(x / reference - 1) if reference else x for x in ratios]
    # Deliberately labelled scale, not a rigorous FFT error bound.
    roundoff_scales = [float(np.finfo(float).eps * max_abs_F * math.log2(grid_size**2)
                            / radius**(2 * i) / C[i]**2) for i in indices]
    return {
        'method': 'direct_function_fft2', 'domain_bound': bound,
        'grid_size': grid_size, 'radius': radius, 'indices': list(indices),
        'coefficients': [float(x.real) for x in coefficients],
        'binomial_coefficients': [C[i] for i in indices], 'ratios': ratios,
        'relative_errors': errors,
        'max_imaginary_ratio': max(abs(float(x.imag)) for x in ratios_complex),
        'max_abs_E_on_grid': max_abs_E, 'max_abs_F_on_grid': max_abs_F,
        'roundoff_ratio_scale_not_bound': roundoff_scales,
        'alias_suppression_per_wrap': radius**grid_size,
        'runtime_sec': perf_counter() - started,
    }
