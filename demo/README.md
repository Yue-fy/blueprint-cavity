# Optional historical UI recorder

The accepted 84-second film is already bundled at `public_delivery/blueprint-film.mp4`; open `/film/` or download the release. See [the current demo guide](../DEMO.md).

`scripts/record_demo.py` is an older recorder for the construction workspace and the separate mathematical toy. It records actual saved trajectories and manual UI interactions; it does not perform live AI inference. Its output is not the accepted product film.

For maintainers who want a fresh recording, install Playwright from the full development lockfile and its Chromium browser, start the local server on port 8430, then inspect its plan:

```sh
.venv/bin/python scripts/record_demo.py --plan
.venv/bin/python scripts/record_demo.py --rehearse
```

The recorder does not launch the server. Actual recording writes ignored `dist/demo/` outputs; MP4 conversion additionally needs FFmpeg. Captured model runs and manual form actions remain distinct. Review any new recording and its provenance before redistributing it. No model provider credentials are needed to replay the bundled data.
