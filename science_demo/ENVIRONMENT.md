# Private optional scientific Harbor candidate

This package contains four generic Case A tasks, `science-a-01` through
`science-a-04`, built from `parameters.json` and separate from the 36 drawing
tasks and their evaluation results. The generic toy proof and numerical checks
passed independent scientific review. Original research applications remain
unvalidated, and original scientific projects, posts, models and datasets are
excluded. The audience remains private; public use has not been approved.

The explicitly authorized generic Verda/Modal evaluation completed 16 trials;
see [EVALUATION.md](EVALUATION.md) and [RESULTS.md](RESULTS.md) for scope,
results and limitations. Frozen evaluated `task.toml` files retain historical
pending-review labels from their original capture; those labels do not describe
the subsequent review and authorization and the task files were not regenerated.

The builder consumes `science_demo.toy.reference_limit(g, c, A) -> Fraction`.
The exact rational reference, proof, and numerical validation are host-side
material maintained separately. Local oracle checks alone establish no model
performance or scientific acceptance claim.

## Local commands

Run from the project root, using the project's existing virtual environment:

```sh
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python science_demo/build_tasks.py
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m pytest tests/test_science_tasks.py -q
```

The builder also accepts `--output-dir PATH` for an isolated local copy. Generation
is deterministic and refuses unexpected existing files or symlinks within a task,
so a stale build context cannot silently include reference material. Resolve a
refusal by reviewing the named directory, then generate into a fresh directory.
Run one local job at a time, with niceness 15 and one numerical thread; these
checks require no GPU and stay below 0.5 GB locally. The local tests do not build
images, invoke agents, use model APIs, or start Harbor/Modal/cloud jobs.

For one offline oracle check, choose a temporary output directory:

```sh
mkdir -p /tmp/science-private-local
sh science_demo/tasks/science-a-01/solution/solve.sh /tmp/science-private-local/answer.json
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -I science_demo/tasks/science-a-01/tests/verify.py \
  --gold science_demo/tasks/science-a-01/tests/gold.json \
  --answer /tmp/science-private-local/answer.json \
  --output-dir /tmp/science-private-local/logs
```

`reward.txt` and `breakdown.json` are written to the selected output directory.
The oracle's optional path argument is only for local checks; without it the
script writes the Harbor handoff artifact `/workspace/answer.json`.

## Harbor boundary and resource limits

The layout targets Harbor 0.26.0, task schema 1.4. Each task contains
`instruction.md`, `task.toml`, `environment/`, `tests/`, and `solution/solve.sh`.
The agent build context contains exactly `Dockerfile` and neutral `input.json`
parameter strings. Its Dockerfile copies only `input.json`. It preinstalls Python,
NumPy 2.2.6, Node/npm, and OpenCode 1.19.5. Package installation requires
network access during image builds. The recorded generic provider evaluation
built images on Modal. Agent settings are 600 seconds, one CPU, 2 GB memory,
and no GPU.
The agent has public network mode to support the authorized generic model
provider connection. This setting alone does not authorize further runs.

The separate verifier has no network, one CPU, 256 MB memory, and a 60-second
Harbor timeout. Its scoring code uses only Python's standard library, and local
verifier invocations are checked to finish within five seconds. Harbor transfers
only `/workspace/answer.json` as the declared artifact. Verifier gold and oracle
solutions remain outside the agent build context; neither the reference module,
proof, validation records, historical formula, nor research records are copied
there. The generator source is host-side code, not an agent input.

The completed provider runs were explicitly authorized for the generic toy only.
Any additional provider work requires its own authorization and resource budget.
Do not publish this package or broaden its private audience without approval.

## Answer and scoring contract

Submit exactly `value`, `confidence`, and `rationale` in a UTF-8 JSON object at
`/workspace/answer.json`. `value` is a finite number or explicit `null`;
`confidence` is a finite number in [0,1]; `rationale` is a string and its semantic
content is ungraded. The maximum artifact size is 1 MiB. Missing/malformed JSON,
duplicate keys, boolean numbers, nonfinite numbers including `1e999`, and
nonregular or symlink artifacts earn zero total credit.

Numerical credit is 1 through relative error 0.001, decreases linearly to 0 at
relative error 0.05, and is 0 thereafter. Calibration uses
`1 - (confidence - correct)^2`, where `correct` means numerical credit at least
0.99. Total reward is `0.90 * numerical_credit + 0.10 * calibration`. An explicit
`null` with confidence 0 can earn 0.10; a missing answer earns 0. The A=0 case is
a control where the private counterfactual formula coincides with the reference;
it is not designated a trap.
