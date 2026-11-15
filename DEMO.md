# Demonstrate Blueprint + Cavity

Use the [public demo](https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/) or start the complete local site with the commands in [README.md](README.md). Both case entries are on the first screen.

The [English review guide](docs/REVIEW_GUIDE.md) provides 2–4 minute and 10 minute routes. The [Chinese walkthrough PDF](docs/JUDGE_WALKTHROUGH.zh-CN.pdf) contains the detailed sequence and evidence boundaries.

- Blueprint: follow `bp-01-clean`, inspect the saved 29.1 m² / 26.4 m² submissions against the 26.9 m² reference, then try the human workspace.
- Cavity: read the physical introduction, open the linewidth-window experiment and compare the 52.7 / 96.4 estimates. The reply checker works with pasted test text without calling a model.
- Inspect Results for all 144 historical construction trials. The mathematical toy's 16 trials remain separate.

For an offline scoring audit:

```sh
.venv/bin/python scripts/judge_check.py
```

The accepted product film is 84 seconds, with music and burned English captions. It is bundled at `public_delivery/blueprint-film.mp4`, viewable at `/film/`, and downloadable from [Release v1.0.0](https://github.com/Yue-fy/blueprint-cavity/releases/tag/v1.0.0). All credits are in [submission/CREDITS.txt](submission/CREDITS.txt).

An older optional UI recording script remains documented in [demo/README.md](demo/README.md). It is not the renderer for the accepted 84-second film.
