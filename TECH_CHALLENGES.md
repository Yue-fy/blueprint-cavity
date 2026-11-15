# Tech Challenge Participation — Blueprint + Cavity

**Recommended selections: Verda Compute Track / Best use of Verda, Modal, and OpenAI Codex.**

[Try the public product](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/) · [Source code](https://github.com/Yue-fy/blueprint-cavity) · [Film](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/film/) · [Presentation and downloads](https://github.com/Yue-fy/blueprint-cavity/releases/tag/v1.0.0)

Prepared on **15 November 2026** for the Junction submission. This document explains the technology actually used and provides supporting evidence. It is not a claim that the platform form has already been submitted or that a sponsor has confirmed an award eligibility decision.

## What to select

| Technology challenge | Recommendation for this project | Actual use / reason |
| --- | --- | --- |
| **Verda Compute Track / Best use of Verda** | **Select** | Verda's OpenAI-compatible inference API served the Kimi and DeepSeek agents in the recorded evaluations. Verda's announcement explicitly includes projects using any of its services; a self-managed GPU instance is not our claimed usage. |
| **Modal** | **Select** | Modal provided the remote Harbor execution environment for the recorded agent and verifier trials. |
| **OpenAI Codex** | **Select** | Codex was used as a development assistant for product refinement, parallel implementation/review work, documentation, validation and public delivery. It is separate from the models evaluated inside the environment. |
| **NVIDIA Nemotron** | **Do not select on the current evidence** | The retained model evaluations use Kimi and DeepSeek. No Nemotron run or integration is documented. Using Verda or Modal does not by itself demonstrate Nemotron use. |
| **Gemini API** | **Do not select on the current evidence** | No Gemini API integration or model run is documented. |
| **Atech** | **Do not select on the current evidence** | No qualifying Atech integration is documented. Its additional sharing requirement would not establish actual technology use by itself. |
| **Cloudinary** | **Do not select on the current evidence** | Images, video and downloadable assets are bundled with the product or delivered through GitHub; no Cloudinary integration is documented. |

Match these names to the options displayed by the submission platform. The main **AfterQuery / Break the Agent** challenge is a separate selection from these technology awards.

## Copy-ready participation statement

> We used Verda Inference to run Kimi and DeepSeek through Harbor/OpenCode on 36 construction tasks, retaining 72 model attempts with inspectable tool replays and rewards. Modal provided the remote execution environment for the agent and verifier trials. Codex supported the development and review of the product interface, parallel Blueprint/Cavity presentation, documentation, validation and public release. Verda supplies model inference, Modal supplies evaluation execution, and Codex supports the development workflow. We are submitting for these three technology challenges. The public evidence and usage report are available at https://github.com/Yue-fy/blueprint-cavity/blob/main/TECH_CHALLENGES.md.

## Verda: model inference used in the actual evaluation

### What we used

The retained construction evaluation configurations use the endpoint `https://inference.verda.com/v1`, the OpenAI chat-completions format, and these model identifiers:

| Model in the recorded configuration | Construction attempts | Mean verifier reward |
| --- | ---: | ---: |
| `verda/kimi-k3-1-pro` | 36 | 0.807308 |
| `verda/deepseek-4-1-flash-1017` | 36 | 0.392409 |

These are **rewards, not accuracy percentages**. The full construction record contains 144 trials: the 72 model attempts above, 36 privileged gold-reference oracle trials and 36 no-op trials. Oracle/no-op controls are not additional Verda model attempts.

### How we used it and why it mattered

1. Prepared 36 tasks covering 12 construction scenarios in vector-PDF, clean-image and explicitly synthetic-scan conditions. Agents receive a drawing and work order and can inspect files, render images, use OCR, calculate geometry and write an answer.
2. Connected the OpenCode agent to Verda through its OpenAI-compatible provider configuration. The retained setup uses Harbor 0.26.0 and OpenCode 1.19.5; it does not require a custom model adapter.
3. Evaluated both models on the same task collection, with two concurrent trials configured per model job. Saved submissions, rewards, warnings and sanitized tool trajectories make the comparison inspectable.
4. Used the observed decisions to explain a concrete failure. On the demonstrated fitness-room task, DeepSeek submitted **29.1 m²**, Kimi submitted **26.4 m²**, and the reference is **26.9 m²**. The replay records a boundary assumption that helps explain the discrepancy.
5. Exposed the drawing, recorded actions and scoring breakdown in the human interface. A visitor can submit a measurement to the same scorer and inspect why a result receives its reward.

Verda supplied the inference needed to measure real agent behavior. We do not claim to have provisioned Verda GPU instances, trained model weights, or measured a cost saving. Recorded inference costs are unavailable, not zero. Each model/task pair has one recorded formal attempt; three independent repeats have not been performed.

A separate four-task mathematical toy has 16 historical trials, including eight model attempts and two DeepSeek timeouts retained as zero rewards. Those results are separate from the construction matrix and do not validate the hBN cavity.

### Public evidence

- [Kimi evaluation configuration](configs/evaluation-full-kimi.json) and [DeepSeek evaluation configuration](configs/evaluation-full-deepseek.json): provider endpoint, model names, Modal environment and concurrency.
- [Construction results](RESULTS.md) and [machine-readable ledger](data/results.json): complete denominators, means, warning counts and limitations.
- [DeepSeek fitness-room replay](data/trajectories/full-deepseek-bp-01-clean.json) and [Kimi fitness-room replay](data/trajectories/full-kimi-bp-01-clean.json): saved actions and submitted answers.
- [Separate mathematical results](science_demo/RESULTS.md): the independent toy evaluation and its timeouts.

### Submission route

Document the usage and submit through the **Junction platform**. Verda's own announcement says projects using any Verda service can participate and asks teams to document their process and submit via the official platform. The announcement does not state a mandatory Discord project post. This report supplies the usage documentation; publishing it does not replace selecting the award and submitting the platform form. [Verda announcement](https://verda.com/blog/junction-2026) · [Participant rules](https://hackjunction.app/participate/45/tech-challenges/56)

## Modal: remote execution for repeatable evaluation

### What we used

The retained construction configurations set `environment.type` to `modal`. Harbor used remote execution environments for the tool-using agents and verifier work. The recorded model configuration sets a 1,200-second sandbox timeout, a 60-second verifier override, two concurrent trials per model job, and environment deletion after use.

### How it supported the product

- **Execution:** agents could run drawing inspection and calculation tools in remote environments while sending model requests to Verda.
- **Control runs:** the canonical oracle and no-op configurations also use Modal. They establish reference scoring behavior alongside the model runs.
- **Operational refinement:** the development record documents increasing the cloud verifier deadline from 15 to 60 seconds after timeouts during verifier-log retrieval. This changed the execution deadline, while preserving the task data, scoring weights and numerical tolerances.
- **Evidence delivery:** the exported results and saved trajectories feed the public replay interface. Judges can inspect the outcomes without holding a Modal account or starting new paid evaluations.

This is a remote-evaluation usage claim, not a GPU-training or infrastructure-performance benchmark. Modal charges are not available in the retained cost data. The future Verda-only network policy has been prepared but has not been verified in a new live Docker/Modal run; historical public-network configurations are not a guarantee against access to now-published answers.

### Public evidence

- [Model execution configuration](configs/evaluation-full-deepseek.json).
- [Canonical oracle configuration](configs/evaluation-full-oracle-verified.json) and [no-op configuration](configs/evaluation-full-nop.json).
- [Results and historical diagnostics](RESULTS.md), including warnings and the distinction between the interrupted first oracle job and the canonical oracle.
- [Development decisions](docs/DECISIONS.md) and [evaluation/reproduction guidance](docs/EVALUATION.md).

### Submission route

Select **Modal** and explain its role in the platform submission, linking this report. The participant-rule summary supplied by the team did not identify a mandatory Discord post. That summary is the basis for this routing guidance; the participant page could not be independently read anonymously during this check. [Participant rules](https://hackjunction.app/participate/45/tech-challenges/40)

## Codex: development, review and delivery

### How we used it

Codex was used in the project workspace to carry out the owner's requested product and submission work:

1. Refined the light product interface and dark scientific canvas, and presented **Blueprint and Cavity as parallel cases** with independent entry points.
2. Coordinated separate implementation, first-impression review, browser-flow review and Chinese-manual work. Feedback was checked against the implementation and recorded evidence.
3. Made the demonstration understandable to a first-time reviewer: a concrete drawing task, visible model decisions and an introduction to the hBN scientific setting.
4. Prepared the detailed Chinese manual, English review route, submission copy, eight-slide English presentation and organized public repository.
5. Ran local verification, inspected the actual PDF pages, checked public links and prepared reproducible validation in GitHub Actions.

This is an account of **development use**. The linked files show the resulting deliverables; raw development conversations are not included in the public release. The reported benchmark models remain Kimi and DeepSeek. **OpenCode is the runtime agent harness component; Codex is the development assistant. They are different tools.**

### Public deliverables and verification

- [Product interface](web/) and [Cavity exhibit](hbn_demo/README.md).
- [Detailed Chinese product manual](docs/PRODUCT_MANUAL.zh-CN.md) and [English review route](docs/REVIEW_GUIDE.md).
- [Presentation source and rendering instructions](docs/presentation/README.md) and [eight-slide PDF](docs/presentation/Blueprint-Cavity-Presentation.pdf).
- [Submission form copy](submission/form-fields.en.txt).
- [Verification workflow](.github/workflows/verify.yml), [offline audit](scripts/judge_check.py) and [evidence-hash check](scripts/verify_evidence.py).
- [Successful verification of the presentation/form release](https://github.com/Yue-fy/blueprint-cavity/actions/runs/43680458139), for source commit `955db7f39377b3249f3a91ef5039388d465db1f5`. This checks the software and retained evidence; it does not run new model trials.

The offline audit checks **240 deterministic fixtures** across 36 construction tasks and four separate mathematical tasks. The hash check verifies **604 frozen evidence files**. Neither number is a count of new AI runs.

### Submission route

Select **Codex** and explain its actual development role, linking this report and the public repository. The participant-rule summary supplied by the team did not identify a mandatory Discord post. That summary is the basis for this routing guidance; the participant page could not be independently read anonymously during this check. [Participant rules](https://hackjunction.app/participate/45/tech-challenges/49)

## Scope of the scientific case

Cavity is a parallel product case with precomputed hBN fields, modes and spectra. The scientific visualization is not evidence of a new solver job on Verda or Modal. Its local pasted-answer checker compares supported numbers against a fixed mathematical reference; it does not call a model API or validate a cavity design. The three technology participation claims above do not turn Cavity into an evaluated online scientific agent.

## Submission requirements and source status

The table below preserves the team's supplied official-rule summary. **Only the Verda sponsor announcement was independently retrieved in this check.** The linked Junction participant pages and Cloudinary form were not accessible to the anonymous tools used here, so their detailed requirements are attributed to the team's supplied summary rather than presented as newly verified. The currently displayed official platform rules govern the actual submission.

| Technology award | Submission route in the supplied rule summary | Source |
| --- | --- | --- |
| Verda Compute Track | Document the usage and submit on Junction. This route is also confirmed by Verda's announcement. | [Platform](https://hackjunction.app/participate/45/tech-challenges/56) · [Verda](https://verda.com/blog/junction-2026) |
| NVIDIA Nemotron | Include which Nemotron model was used, what it did, why it mattered and how its outputs were improved. Discord is described as a support channel. | [Platform](https://hackjunction.app/participate/45/tech-challenges/46) |
| Modal | Select the award and explain the actual use in the description or demo; no mandatory Discord post was listed in the supplied summary. | [Platform](https://hackjunction.app/participate/45/tech-challenges/40) |
| Gemini API | Select the award and explain the actual use in the description or demo; no mandatory Discord post was listed in the supplied summary. | [Platform](https://hackjunction.app/participate/45/tech-challenges/48) |
| Codex | Select the award and explain the actual use in the description or demo; no mandatory Discord post was listed in the supplied summary. | [Platform](https://hackjunction.app/participate/45/tech-challenges/49) |
| Atech | Also share the project-summary link or post in their Discord, as specified by that award's rules. This project is not currently claiming Atech use. | [Platform](https://hackjunction.app/participate/45/tech-challenges/29) |
| Cloudinary | Also complete Cloudinary's separate submission form. This project is not currently claiming Cloudinary use. | [Platform](https://hackjunction.app/participate/45/tech-challenges/41) · [Form](https://cld.media/hackathon-survey) |

Community-page instructions are not treated as an additional official submission requirement. No Discord post, sponsor form or competition submission has been sent as part of publishing this report.

## 中文填表说明

1. **Tech Challenge Participation：建议勾选 Verda、Modal、Codex。** 若 Verda 显示为 `Verda Compute Track` 或 `Best use of Verda`，选择平台对应选项；本项目的实际使用是推理 API，不是自行创建 GPU 实例。
2. 在技术使用说明或相关链接字段填写本页地址：`https://github.com/Yue-fy/blueprint-cavity/blob/main/TECH_CHALLENGES.md`。这是渲染后的 Markdown 阅读页，公开访问，无需密码。
3. 若有说明文本框，可复制上面的 **Copy-ready participation statement**，也可以按奖项分别引用 Verda、Modal、Codex 三节。
4. **NVIDIA Nemotron、Gemini API、Atech、Cloudinary 暂不勾选**：当前交付物没有这些工具的实际使用证据。借助其他云平台或已经制作了图片/视频，不等于使用了对应技术。
5. Verda 公告已确认通过 Junction 平台提交使用记录；其余提交动作按你提供的规则摘要整理，原始官方链接均保留在上表。Atech 的 Discord 和 Cloudinary 的额外表单要求不适用于本次建议勾选的三项。
6. 本页是使用说明与证据材料；仍需在 Junction 表单中实际勾选并提交。项目主挑战继续选择 AfterQuery / Break the Agent。
