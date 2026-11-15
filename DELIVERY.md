# Release delivery

**Repository:** https://github.com/Yue-fy/blueprint-cavity

**Public product:** https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/

**Versioned downloads:** https://github.com/Yue-fy/blueprint-cavity/releases/tag/v1.0.0

The repository is a curated public release with a fresh history. The existing development repository remains private. Local launch uses the included files and does not need cloud credentials.

| Deliverable | Repository path / entry |
| --- | --- |
| Product and Cavity | `web/`, `hbn_demo/index.html`, local root and `/hbn/` |
| 84-second 1080p film | `public_delivery/blueprint-film.mp4`, local `/film/` |
| Full presentation ZIP | `public_submission/blueprint-cavity-submission.zip`, local `/submit/` |
| YouTube and square covers | `public_submission/youtube-thumbnail.jpg`, `cover-square.jpg` |
| Subtitles and upload copy | `public_submission/` and `submission/` |
| 44-page Chinese manual | `docs/PRODUCT_MANUAL.zh-CN.pdf` |
| 10-page Chinese walkthrough | `docs/JUDGE_WALKTHROUGH.zh-CN.pdf` |
| Historical evidence hashes | `docs/FROZEN_EVIDENCE.json` |
| Recorded results | `data/results.json`, separate `science_demo/results.json` |

The presentation ZIP contains 15 files and retains the accepted film bytes, captions, covers, PDFs, upload text and attribution. [Its original delivery manifest](submission/DELIVERY.json) records the exact hashes; `dist/...` paths in that historical manifest describe the original build workspace, while this table gives the public repository layout.

YouTube channel upload is pending. The repository supplies the upload-ready video, English title/description, subtitles and required credits; no YouTube watch URL has been created.

The public edition of the Markdown manuals marks omitted development-source references as archival paths. The PDFs preserve the accepted detailed historical manuals. Follow the current README for installation and the review guide for the public entry points.

The [offline checks](docs/EVALUATION.md) verify code and recorded data. They do not establish new model results, independent repeated attempts, runtime egress enforcement or training improvements.
