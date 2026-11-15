# Diagonal coefficient limit

This is a private optional prototype pending independent scientific review and
user approval for public use.

The real parameters are g = 0.1, c = 0.5,
and A = 1. They are also provided as exact decimal strings in
`/workspace/input.json`.

Define f(u) = A + (1-u)^(3/2), using the branch analytic near u=0
with (1-0)^(3/2)=1. Set E(u,v) = g(c + f(u) + f(v)), and define
F(u,v) = -0.5 * [log(1-E(u,v)) + E(u,v)], using the logarithm branch
analytic at (0,0) and real there. Let a_ii be the coefficient of u^i v^i
in the Taylor expansion of F about (0,0). Let C_i be the coefficient
of u^i in the Taylor expansion of (1-u)^(3/2) about 0.

Determine the limit as i tends to infinity of a_ii / C_i^2.
You may derive the limit or estimate it numerically. Python and NumPy are
available. No external data are needed.

Write one UTF-8 JSON object to `/workspace/answer.json`, with exactly these
three required fields:

- `value`: a finite JSON number giving the limit, or `null` to abstain.
- `confidence`: a finite number between 0 and 1, expressing your probability
  that your numerical answer meets the correctness criterion below.
- `rationale`: a string with your derivation or estimation method. Its content
  is not semantically graded.

The artifact must be at most 1 MiB. Missing files, malformed JSON, duplicate
keys, nonfinite values (including overflowed exponents), and boolean numbers
receive zero total credit.

Numerical credit is 1 for relative error at most 0.001, decreases linearly to
0 at relative error 0.05, and is 0 beyond that. An answer is considered correct
for calibration when its numerical credit is at least 0.99. Calibration credit
is 1 - (confidence - correct)^2, with correct encoded as 0 or 1. The final
reward is 0.90 * numerical credit + 0.10 * calibration credit. Explicitly
abstaining with `value: null` and `confidence: 0` can earn 0.10; a missing
artifact earns 0.
