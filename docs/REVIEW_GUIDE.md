# Review Blueprint + Cavity

[Open the public demo](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/) · [Watch the 84-second film](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/film/) · [Download release assets](https://github.com/Yue-fy/blueprint-cavity/releases/tag/v1.0.0) · [中文 README](../README.zh-CN.md)

Start with either case. **Blueprint** exposes recorded decisions on construction drawings and the verifier that scores them. **Cavity** lets you inspect precomputed nanocavity data, change an analysis window and check numerical claims locally. The cases have equal navigation prominence and separate evidence records.

## A 2–4 minute route

| Time | Action | What to inspect |
| --- | --- | --- |
| 0:00–0:20 | Open the homepage. Find the two **Explore case →** cards and the persistent **Blueprint / Cavity** navigation. | Two entry points; neither case requires completing the other. |
| 0:20–1:20 | Open [Blueprint](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#tour/1). Advance through **The task → The decision → The comparison → The score**. | Task `bp-01-clean`: DeepSeek **29.1 m²**, Kimi **26.4 m²**, reference **26.9 m²**. DeepSeek's saved assumption treats the lower horizontal line as furniture/equipment. Inspect the highlighted boundary and the quantity/evidence/confidence breakdown. |
| 1:20–1:50 | Click **Replay DeepSeek’s saved run** or open **Results → Replay DeepSeek’s decision**. | A saved tool/answer record, not live inference. The reported boundary assumption is visible in the actual record. |
| 1:50–2:40 | Open [Cavity](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#cavity), then [the window experiment](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/#tab=4). Change the selected spectral window. | The spectrum stays fixed while the linewidth and Q estimate change. Read the window warning; a narrower window is not automatically a better physical estimate. |
| 2:40–3:30 | Open [the local reply checker](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/#tab=5&live=1). Paste `ANSWER: 0`, then click **Check reply**. Replace it with `VERDICT: INCORRECT` and check again. | The first produces a numerical mismatch; the second asks for manual formula/reasoning review. These are deliberate reviewer test inputs, not recorded model answers. No model account is needed. |
| 3:30–4:00 | Return to [Results](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#results). | Read the model means and the historical denominators below. |

If only two minutes are available, show the Blueprint comparison and score, then switch directly to Cavity's window experiment. The film is an optional introduction focused on one Blueprint task; it does not replace reviewing the parallel Cavity case.

## A 10-minute hands-on route

| Minute | Action | Checkable outcome |
| --- | --- | --- |
| 0–1 | Open **Cases**, briefly enter each case, then start the Blueprint four-step tour. | Both cases are discoverable from the same page. |
| 1–2 | Inspect **The decision** and **The comparison** for `bp-01-clean`. | Compare 29.1 / 26.4 / 26.9 m² and the actual saved boundary assumption. Do not infer a cause solely from the reward. |
| 2–3 | Open a saved replay and inspect the submission and one tool observation. | The model observes drawing files, uses tools and writes an answer with supporting evidence. Original records: [DeepSeek](../data/trajectories/full-deepseek-bp-01-clean.json), [Kimi](../data/trajectories/full-kimi-bp-01-clean.json). |
| 3–4 | Choose **Try it yourself** or [open the same workspace](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#workspace/bp-01-clean). Pan/zoom; choose **Mark evidence** and draw a supporting region. Enter a quantity, unit and confidence, then **Verify my takeoff**. | The human submission uses the actual verifier. Evidence coordinates stay in the original drawing space. On a phone, switch between **Drawing** and **Your takeoff**. |
| 4–5 | Inspect reward components, then **Reveal reference solution**. | Reward weights are value **0.75**, evidence **0.15**, calibration **0.10**. Evidence credit is gated by numerical performance. If you used the already-revealed 26.9 m², identify this as a scorer demonstration, not an independent measurement. |
| 5–6 | Switch to **Cavity**, enter the full lab and explore the [stored modes](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/#tab=1). | Inspect precomputed fields and view controls. Changing the view does not run a new solver. |
| 6–7 | Open [Pick your box](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/#tab=4). Compare a broad window with a narrower one. | The same saved spectrum can yield different linewidth/Q estimates. The demonstrated full/narrow selections give approximately **52.7 / 96.4**; arbitrary dragged bounds need not reproduce those exact values. |
| 7–8 | Open [AI reviews AI](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/#tab=5&live=1). Check `ANSWER: 0`, then `VERDICT: INCORRECT`. Close with **Close (Esc)** at the top of the dialog. | Numerical mismatch and manual-review states are distinct. The checker does not score a proof or validate a cavity design. |
| 8–9 | Return to **Results** and compare the table below. Optionally open the separate [/science/ mathematical case](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/science/). | Construction: 144 trials. Mathematical toy: 16 separate trials. Cavity fields: outside both matrices. |
| 9–10 | Run the offline audit below from the repository root; inspect its PASS line and complete history counts. | 240 deterministic fixtures and an audit of saved results, without a provider call or a new model evaluation. |

## Run the local check

Use **Python 3.12**. This audit uses only the Python standard library:

```bash
python3 scripts/judge_check.py
```

Expected first line:

```text
PASS: 40 tasks × 6 offline controls; reference 1, noop 0, stop-early 0.10.
```

The six controls per task are reference, no-op, explicit-abstention stop-early, confidently wrong, duplicate JSON keys and an overflowing number. The final three receive zero. Stop-early here is an explicit abstention fixture, not an interrupted model trajectory. The script also verifies the full 36/4-task historical denominators and rejects missing, duplicate or unfinished records when calculating complete means. See [the audit implementation](../scripts/judge_check.py) and [the construction scorer](../blueprint_gym/scoring.py).

To run the human interface locally:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-demo.txt
bash scripts/serve.sh
```

Open **http://127.0.0.1:8430/**. Use the same hash routes as the public site, for example `/#tour/1`, `/#workspace/bp-01-clean` and `/#cavity`. Keep the terminal running; Ctrl+C stops the server. Initial dependency installation needs internet access. The audit and local demonstration require no inference key, GPU or new paid trial.

## Read the evidence with its denominator

| Suite / group | Recorded trials | Mean verifier reward |
| --- | ---: | ---: |
| Blueprint — Kimi | 36 | 0.807308 |
| Blueprint — DeepSeek | 36 | 0.392409 |
| Blueprint — privileged gold-reference oracle | 36 | 1.000000 |
| Blueprint — no-op | 36 | 0.000000 |
| Separate mathematical toy — Kimi | 4 | 0.750000 |
| Separate mathematical toy — DeepSeek | 4 | 0.253368 |
| Separate mathematical toy — oracle | 4 | 1.000000 |
| Separate mathematical toy — no-op | 4 | 0.000000 |

The construction matrix has **36 tasks / 144 trials / 72 actual model replays**. Each model/task pair has one recorded formal attempt. The mathematical toy has **4 tasks / 16 trials**, including **8 model attempts**; its two DeepSeek timeouts remain zero in the denominator. Sources: [construction results](../data/results.json), [mathematical results](../science_demo/results.json).

These values are **rewards, not accuracy percentages**. The historical oracle has privileged access to gold; its perfect reward is a reference ceiling, not a same-input learned strategy. Three independent model repeats have not been completed, and no model weights have been trained. Cavity's precomputed physics and local numeric checker are not evidence of an online scientific agent or a new physical validation.

## What to examine against the judging criteria

| Criterion | Concrete review action | What the current evidence supports |
| --- | --- | --- |
| Performance gap · 30 | Compare complete means, then inspect both `bp-01-clean` submissions. | A historical model/reference gap and traceable examples; repeated-run robustness remains unmeasured. |
| Meaningful difficulty · 30 | Read the [task](../tasks/bp-01-clean/) and inspect the drawing boundary, scale and saved tools. | Practical measurement and interpretation decisions, using available drawing information and tools. |
| Reward integrity · 25 | Submit in the workspace and run the six-control audit. | Deterministic value/evidence/calibration scoring and explicit malformed-answer/abstention behavior. |
| Craft · 15 | Run the standard-library audit, start the local server, and follow both cases on desktop or mobile. | An inspectable repository, usable interface, saved replays and documentation. |

The published website and repository include reference answers and replays. They are review material, not a secret held-out benchmark; future evaluations need their own verified isolation and independent records. The 240 offline fixtures establish verifier behavior, not three new model repeats.

For further detail, use the [Chinese product manual PDF](PRODUCT_MANUAL.zh-CN.pdf), [Chinese 10-minute guide PDF](JUDGE_WALKTHROUGH.zh-CN.pdf), and [v1.0.0 release downloads](https://github.com/Yue-fy/blueprint-cavity/releases/tag/v1.0.0).
