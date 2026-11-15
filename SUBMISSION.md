# Submission: Blueprint + Cavity

## Project name

Blueprint + Cavity

## Punchline

Two cases for checking AI work: recorded construction takeoff with inspectable rewards, and precomputed nanocavity physics with local checks of numerical claims.

## Description

<!-- submission-description:start -->
Blueprint + Cavity makes AI work inspectable through two parallel cases with different levels of evidence.

Blueprint is a construction takeoff environment for Harbor. An agent receives a licensed drawing and work order, inspects PDFs or images, uses terminal tools for rendering, OCR and geometry, and submits a quantity, unit, confidence, evidence rectangles and assumptions. The decisions are practical: recover scale, identify the correct boundary, deduct openings and distinguish printed elevations from measured areas. The 36 tasks cover 12 scenarios in vector, clean-image and explicitly synthetic-scan conditions, across five takeoff families.

A deterministic offline verifier combines value (75%), evidence (15%) and confidence calibration (10%). Evidence credit is gated by the numerical result. Compatible units and documented alternatives are accepted; malformed answers earn zero. A no-op earns zero, and valid abstention can earn at most 0.1. The human workspace uses the actual scorer, so judges can measure, submit, reveal a reference and inspect the resulting reward.

The historical core matrix contains 144 completed trials: 36 DeepSeek, 36 Kimi, 36 privileged gold-reference oracle and 36 no-op. The 72 model trials have actual saved replays. Mean rewards are DeepSeek 0.392409, Kimi 0.807308, oracle 1.000000 and no-op 0.000000. Rewards are not accuracy percentages. The oracle demonstrates the verifier's reference ceiling; it is not a fair same-input learned baseline. Each model/task pair has one recorded formal attempt, not three independent repeats. For one fitness-room task, DeepSeek submits 29.1 m² and Kimi 26.4 m² against a 26.9 m² reference; the replay exposes a boundary assumption behind the error.

Cavity is a separate scientific interface for precomputed hBN nanocavity fields, modes, spectra and linewidth-window sensitivity. Its local checker can inspect numerical fields pasted from an AI reply and flag discrepancies. It makes no live model calls, launches no new physical simulation and does not verify a scientific proof. Cavity is not part of the construction benchmark. A separate four-task mathematical toy has its own 16 historical trials; those results are not hBN validation.

The public, responsive site gives both cases equal entry points, with guided interaction, a results ledger, recorded trajectories and a Chinese manual. The 84-second captioned film follows one Blueprint task and introduces Cavity. The drawing sources, answer provenance and licensing are documented. The construction variants share source drawings, so this is an auditable environment demonstration, not an unseen-building generalization claim.

For review, an offline audit checks historical completeness and 240 deterministic verifier fixtures. A separate command prepares fresh reference, three-agent-attempt, no-op and stop-early trials with source/derived hashes and a Verda-only agent network policy; execution requires an explicit flag. That future protocol has not yet been run, and runtime egress enforcement remains unverified. Historical public-network configurations may access now-published answers. No model weights have been trained and no post-training improvement is claimed.

Try both cases without a login:
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/
<!-- submission-description:end -->

## Judge command

Prepare the complete reference / three model attempts / noop / stop-early protocol offline:

```sh
python scripts/judge_protocol.py --suite core --model deepseek --environment docker --run-id judge-core-review
```

This creates fresh task copies with agent networking restricted to `inference.verda.com`, retains the separate no-network verifier and records original/derived hashes. The default starts no containers or provider calls. After installing the pinned Python 3.12 environment, Docker Engine/Compose and setting `VERDA_INFERENCE_API_KEY`, use a fresh run ID plus `--execute` to start paid runs. Modal also requires its credentials. Actual runtime egress and provider connectivity remain unverified for this policy. Historical direct configs used public networking; do not present them as isolated after publication of the human answer/replay site.

For the human demonstration, open [Blueprint + Cavity](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site). The owner has authorized anonymous, password-free access to the complete existing demo and hBN data. Choose the Blueprint guided fitness-room task or the parallel Cavity introduction. The two cases have distinct evidence scopes: recorded model evaluation for Blueprint, and precomputed research exploration with a local numerical checker for Cavity. The curated public repository and current download routes are documented in [DELIVERY.md](DELIVERY.md). The original development repository remains private. The hBN exhibit is a separate precomputed research extension, not part of the 160-trial evaluation.

## Resources actually used

- **Verda:** OpenAI-compatible inference for the completed DeepSeek and Kimi construction/scientific evaluations.
- **Modal:** remote agent and verifier containers, including all 36 core oracle trials scoring 1.0. The local Docker route remains untested here.
- **Harbor / OpenCode:** Harbor 0.26.0, schema 1.4, OpenCode 1.19.5 preinstalled, native `snapshot: false`. No custom adapter patch or GPU training.

## Video

The [current 84-second film](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/film/) follows one real fitness-room task, recorded AI actions and a concrete boundary error. It then explains hBN before showing the separate research explorer. English on-screen captions, licensed Scott Buckley music and a public-link/QR ending accompany the 1080p/30fps MP4. There is no live inference, internal command ending or production-tool watermark. [DEMO.md](DEMO.md) supplies the live walkthrough; [video/DELIVERY.json](video/DELIVERY.json) records exact output hashes and credits.

## Captain's submission notes

The name limit is 30 characters, punchline 200 and description 5000. Recheck limits if editing. The completed construction matrix is 36 tasks / 144 trials; science is four tasks / 16 separate trials. Hosting now serves these reviewed final exports. Regenerate the final judge archive after the source/metadata check. Include sanitized scored run evidence and the separate video deliverable; raw logs remain private.

Multi-main-track eligibility was confirmed by the captain. Sponsor guidance permits the README-specified models and local Docker/Compose. The owner authorized private online demonstration and the generic Case A scope recorded in [science_demo/authorization.json](science_demo/authorization.json). The owner subsequently authorized public display of the existing full hBN demo and its embedded data; original raw research files stay excluded. Confirm the demo slot/timezone, upload mechanism, network and judge access logistics before the ten-minute presentation.
