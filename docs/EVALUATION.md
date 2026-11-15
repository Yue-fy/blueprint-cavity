# Evaluation and reproduction

The product separates three kinds of evidence: a recorded construction benchmark, a small mathematical toy, and a precomputed hBN research exhibit. Their rewards and denominators are not interchangeable.

## Recorded construction benchmark

- 36 tasks: 12 scenarios × vector PDF / clean image / synthetic scan, across five families.
- 144 historical trials: 36 each for DeepSeek, Kimi, privileged gold-reference oracle and no-op.
- 72 actual model replays. Each model/task pair has one recorded formal attempt.
- Mean rewards: DeepSeek 0.392409, Kimi 0.807308, reference 1.0, no-op 0.0.
- Two DeepSeek trials have warnings. The complete denominator remains visible in [results](../data/results.json) and [the report](../RESULTS.md).

The oracle reads privileged gold and checks the scoring ceiling. It is not a trained same-input baseline. Shared drawings, reserved scenarios that were inspected during curation, and artificial image degradation do not demonstrate generalization to unseen buildings.

## Mathematical toy and Cavity

The [mathematical toy](../science_demo/ENVIRONMENT.md) has four tasks and 16 historical trials, including eight model attempts. Two DeepSeek timeouts remain zero in the denominator. Its analytic reference derives the answer from the same neutral inputs. See its [results](../science_demo/results.json) and [proof](../science_demo/proof.md).

[Cavity](../hbn_demo/README.md) uses owner-authorized precomputed fields and spectra. Its browser-local checker checks supported pasted numerical claims. Cavity is outside both evaluation matrices; no hBN agent benchmark, live physical simulation or proof verification is claimed.

## Offline checks

With Python 3.12, from the repository root:

```bash
python3 scripts/verify_evidence.py
python3 scripts/judge_check.py
```

These commands need no credentials or third-party package. The first verifies 604 frozen files against [their hashes](FROZEN_EVIDENCE.json). The second checks 40 tasks × six fixtures: reference, no-op, explicit stop-early abstention, confident wrong, duplicate keys and overflowing numbers. It also checks the historical ledgers. Expected control rewards include reference 1, no-op 0 and explicit abstention 0.1.

Fixtures are deterministic software checks, not new model trajectories. Stop-early here is explicit abstention after an observation, not a physically interrupted model run.

## Prepare a new protocol

```bash
python3 scripts/judge_protocol.py --suite core --model kimi --environment docker --run-id review-core
```

The default prepares new task copies and four configurations in `runs/judge-configs/review-core/`. It plans one reference, three model attempts, one no-op and one stop-early trial per task (216 core trials). Use `--suite science` for the separate four-task suite (24 trials), or `--model deepseek` for that model. Run IDs must be fresh; existing output is not overwritten.

Derived tasks carry source and output hashes. Agent networking is restricted in configuration to `inference.verda.com`, and the trusted verifier has a separate no-network policy. Actual Docker/Modal egress enforcement and provider connectivity have not been verified for this policy. The repository and website deliberately publish reference answers and traces, so neither configuration nor networking establishes that these tasks are unseen by a model.

Execution requires the pinned Harbor environment (`requirements.lock`), a supported container runtime and `VERDA_INFERENCE_API_KEY` in the process environment. Modal additionally needs `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. Adding `--execute` starts provider work and may incur cost. No execution, training or GPU job occurs during the local website, offline audit or CI.

Historical configs under `configs/` retain their original public networking. Use the protocol generator for new review runs rather than treating those historical configs as an isolated evaluation setup. Preserve the original captured ledgers; inspect new per-trial artifacts and warnings before reporting another result.

## Exporting new local results

`scripts/export_results.py` is an optional maintainer tool for explicitly named local `runs/raw/<job>` folders. It replaces `data/results.json` and selected replay files; run it in a separate working copy, never to relabel the captured release. It redacts secret-valued process environment variables. An additional dotenv file is read only when explicitly passed with `--redaction-env /path/to/file`; no host-specific credential path is consulted. Review every new export before publishing it.

Three independent model repeats, live validation of the new network policy, and model-weight training remain outstanding research work. The present release does not claim those outcomes.
