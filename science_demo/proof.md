# Private Case A: independent toy derivation and numerical check

This document proves the statement for the mathematical definitions below. It does not independently establish the historical authorship or sequence of research mistakes. No original research code, remote logs, or lattice-model results were accessed or rerun. The owner approved the generic mathematical toy demonstration/publication, independently rewritten code, numerical outputs, and validation using Verda or Modal on 2026-11-15; the scope is recorded in `authorization.json`. This copy remains owner-private. Original scientific projects, research posts and identities, unpublished material models and research datasets, and raw scientific-server files and logs remain private and excluded. This permission note was updated after the numerical evidence was generated; its measured cases and recorded runtimes were not changed.

## Definitions and analytic conditions

Put `q(u)=(1-u)^(3/2)` on the branch analytic at `u=0`, `f(u)=A+q(u)`,
`E(u,v)=g(c+f(u)+f(v))`, and

\[
H(z)=-\tfrac12\{\log(1-z)+z\},\qquad F(u,v)=H(E(u,v)).
\]

Let `a_ii=[u^i v^i]F` and `C_i=[u^i]q(u)`. Parameters here are real rationals represented by exact decimal strings. A sufficient condition used throughout is

\[
B=|g|\left(|c|+2|A|+2\,2^{3/2}\right)<1.
\]

For `|u|,|v|<=1`, this implies `|E|<=B<1`. Thus the logarithm has the analytic branch defined by its power series, there are no zeros of `1-E`, and there are no extra logarithmic singularities in the closed bidisk. The only branch points relevant to coefficient asymptotics are `u=1` and `v=1` from `q`. This is a sufficient condition, not a characterization of all permissible parameters.

The strict margin also permits a radius `R>1`, close enough to 1 that
`|g|(|c|+2|A|+2(1+R)^(3/2))<1`. Consequently `F` extends analytically and stays bounded on the product of disks `|u|,|v|<R` slit along the real rays starting at 1, with the indicated branches. This enlarged slit domain excludes other singularities when deforming both Cauchy contours. A local formal expansion alone would not establish that exclusion.

The code makes the domain decision with rational arithmetic: write
`d=1-|g|(|c|+2|A|)`. The condition is equivalent to `d>0` and
`d^2>32g^2`. The reported floating-point `domain_bound` is only its displayed value; the accept/reject decision does not depend on rounding `sqrt(2)`.

## Full-boundary expansion

The full boundary value is `E_*=g(c+2A)`. Expanding the analytic outer function around this value gives

\[
F=H(E_*)+gH'(E_*)(q(u)+q(v))
  +\frac{g^2}{2}H''(E_*)(q(u)+q(v))^2+\cdots.
\]

Since

\[
H''(z)=\frac{1}{2(1-z)^2},
\]

the coefficient multiplying `q(u)q(v)` is

\[
K=g^2H''(E_*)=\frac{g^2}{2[1-g(c+2A)]^2}.
\]

Terms depending on only one variable have zero diagonal coefficient for `i>0`. It remains to justify why the other mixed terms cannot contribute at the same order.

## Higher terms and the actual diagonal limit

Near `(u,v)=(1,1)`, expand `F` as a convergent power series in `q(u),q(v)`. Across the cut `u=1+x`, the boundary values of `q` have opposite signs and magnitude `x^(3/2)`. The same holds in `v`. The double discontinuity of `F` therefore selects only terms with an odd positive power in *each* of `q(u),q(v)`. Terms with even powers are analytic across the corresponding cut. The first surviving term is `K q(u)q(v)`. The next possible exponents are `(3,1)` and `(1,3)`, so the double discontinuity of the remainder is bounded, locally, by a constant times

\[
x^{9/2}y^{3/2}+x^{3/2}y^{9/2}.
\]

This argument treats the convergent local series as a whole; it does not interchange an uncontrolled infinite sum of asymptotic equivalents.

Deform both coefficient contours to the two cuts and outer arcs in the enlarged slit disks. Terms involving an outer arc, or portions of a cut bounded away from 1, are exponentially small in at least one index. On the local cuts, the Cauchy kernel is `(1+x)^(-i-1)(1+y)^(-i-1)`. The elementary estimate

\[
\int_0^\delta x^\beta(1+x)^{-i-1}\,dx=O(i^{-\beta-1})
\quad (\beta>-1)
\]

then gives a remainder `O(i^-8)` after subtracting the exact term `K C_i^2`. Also

\[
C_i=\frac{\Gamma(i-3/2)}{\Gamma(-3/2)\Gamma(i+1)}
\sim\frac{i^{-5/2}}{\Gamma(-3/2)},\qquad
\Gamma(-3/2)=\frac{4\sqrt\pi}{3}.
\]

It follows that, for each fixed admissible parameter set,

\[
\frac{a_{ii}}{C_i^2}=K+O(i^{-3}),\qquad
\boxed{\lim_{i\to\infty}\frac{a_{ii}}{C_i^2}
=\frac{g^2}{2[1-g(c+2A)]^2}}.
\]

The `O(i^-3)` statement concerns exact coefficients, not finite-grid floating-point output. At `g=0`, all coefficients and the limit are exactly zero.

Expanding around `gc` while discarding the constant parts of `f` loses the nonzero `2A` boundary contribution. The discarded higher terms in that expansion contain factors of `A` multiplying `q(u)q(v)` and must be resummed. The expression `g^2/(2(1-gc)^2)` is therefore wrong in general. At `A=0` it agrees identically and cannot discriminate the error.

## Numerical method and evidence

`toy.estimate_diagonal` directly samples the defining `E` and `F`, then applies `numpy.fft.fft2`. For `M` equally spaced points on each circle of radius `r=exp(-4/M)`, the extracted coefficient is

\[
\widehat a_{ii}=\frac{\operatorname{FFT2}(F)_{ii}}{M^2r^{2i}}.
\]

The binomial recurrence is `C_0=1`, `C_i=C_(i-1)(i-5/2)/i`. The closed-form reference enters only after the numerical coefficients have been computed, to report relative errors. As an additional independent check, differentiation at the origin gives `a_11=9/242` and `a_11/C_1^2=2/121` for `(g,c,A)=(0.1,0.5,1)`; this differs substantially from the limiting `2/225`. The test exercises that actual low-order coefficient.

In exact arithmetic the FFT aliases coefficients as

\[
\widehat a_{ii}=\sum_{k,l\ge0}a_{i+kM,i+lM}r^{M(k+l)}.
\]

The first wrap factor is `exp(-4)`, approximately 0.0183. The additional coefficient decay makes its effect smaller, but this factor by itself is not an error bound. Smaller radii suppress aliases more and amplify roundoff through `r^(-2i)`; larger indices also divide by the rapidly decreasing `C_i^2`. The artifact records an epsilon-based roundoff scale `eps * max|F| * log2(M^2) * r^(-2i) / C_i^2`. It is a diagnostic scale, **not a rigorous bound** or a certified confidence interval.

The checked-in `validation.json` contains freshly computed output for the four immutable parameter sets, `i=(80,100,120)`, and `M=1024`, with a comparison against `M=512` using the same radius rule. In the recorded run:

| Case | Exact reference | Maximum observed relative error | Maximum grid-relative change |
|---|---:|---:|---:|
| a-01 | 2/225 | 1.296e-4 | 4.400e-4 |
| a-02 (A=0 control) | 2/361 | 1.264e-4 | 4.499e-4 |
| a-03 | 49/12482 | 1.349e-4 | 4.483e-4 |
| a-04 (negative g) | 6050/1515361 | 1.301e-4 | 4.511e-4 |

All satisfy the specified `1e-3` target. The measured error generally **increases** across these three indices at fixed `M`; these data do not show finite-index convergence. This is consistent with growing alias/roundoff sensitivity, and does not contradict the exact-coefficient limit proved above. The grid comparison changes both `M` and `r`, so it measures their combined sensitivity. Agreement across two grids is empirical evidence, not an interval enclosure. The historical expression differs by approximately 25–41% in the three nonzero-`A` cases; it equals the reference in the control.

The local artifact generation used a single process with numerical-library thread counts set to one and niceness 15. `/usr/bin/time` measured 0.42 seconds elapsed and 81,896 KB peak RSS (environment-dependent). No GPU, cluster job, model call, or network service was used.

Reproduce locally from the project root:

```bash
nice -n 15 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m science_demo.validate
```

The validator reads, but never rewrites, `parameters.json`; its SHA-256 is included in the artifact. The proof validates only this toy and the specified exponent. No generalized exponent, extra singular group, historical research result, or external source is thereby verified.
