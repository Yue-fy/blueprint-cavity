# Generic Case A: evaluation distribution

This archive contains a captured science_demo/results.json and RESULTS.md, not
the host-only science_demo/run_evaluation.py or scripts/evaluation_guard.py.
The host runner and its export subcommand are unavailable in this distribution.
Original scientific projects and raw server files remain excluded. The four
science tasks stay separate from the 36-task/144-trial construction benchmark.
The full public product, film and hBN explorer are delivered through the Site;
the evaluation archive does not bundle those large media/research assets.

For a future judge run, install the pinned Python 3.12 requirements and prepare
fresh task copies with restricted agent networking:

```sh
python scripts/judge_protocol.py --suite science --model deepseek --environment docker --run-id judge-science-review
```

The default only prepares configurations. It performs no model call and starts
no container. The generated protocol records source/derived hashes, allows only
inference.verda.com in the agent environment, and preserves the separate
no-network verifier. It plans reference, three model attempts, noop and an
explicit stop-early control. To execute, use a fresh run ID and add --execute;
this starts paid provider work. Supply VERDA_INFERENCE_API_KEY only through the
process environment. The Modal variant also requires MODAL_TOKEN_ID and
MODAL_TOKEN_SECRET. Do not commit credentials. Both backends run one trial at a
time. Docker requires Engine, Compose and supported Harbor egress controls.

The included configs/judge-docker-science-deepseek.json and other original
configs are historical baselines using public networking. Do not run them as
isolated evaluation after the human answer/replay website has been published.
Use the protocol generator so every control receives the same derived tasks.
Actual Docker/Modal outbound enforcement and provider connectivity have not
been tested for this restriction. No configuration alone establishes a result,
and no network restriction rules out previously memorized public answers.

Inspect each resulting Harbor trial and verifier reward before reporting a gap.
Keep original exports unchanged; new runs are separate evidence. No model
weights were post-trained. The project coordinator must review and rebuild any
sanitized export; no host export command is bundled here.
