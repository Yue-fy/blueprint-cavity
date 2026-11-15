# Blueprint + Cavity presentation

`Blueprint-Cavity-Presentation.pdf` is the submission-ready English deck: **8 pages, 16:9, 2,228,754 bytes**. It is below the form's 20 MB limit. The final page links to the public demo and GitHub repository.

## Rebuild

From the repository root:

```bash
python -m pip install playwright
python -m playwright install chromium
python docs/presentation/render.py
```

The default uses Playwright's installed Chromium. To reuse another installation, pass `--chromium-path /path/to/chromium` or set `BROWSER_EXECUTABLE`. The renderer waits for fonts and images, checks all eight slide bounds, prints native HTML/CSS, and rejects a PDF at or above 20 MB. Output includes `layout-check.json`.

## Content and sources

The deck follows the repository README, evaluation notes and submission description. It distinguishes the 72 recorded model attempts from 144 construction trials, labels the gold-reading oracle as privileged, and states one historical attempt per model/task and no model-weight training. The 240 deterministic scoring fixtures are not model runs. Cavity remains separate from both historical evaluation matrices.

The Cavity reply checker compares pasted numerical fields with a fixed mathematical reference. It does not call a model, verify a proof, or validate the hBN cavity design or its current spectrum.

- The school-plan image is embedded from `data/previews/bp-01-clean.png`; the highlighted extents on page 3 use the saved submitted and reference coordinates.
- The original field visualization is embedded from `web/cavity-preview.png`; it is precomputed, with heights stretched ×6.
- `assets/q-full.png` and `assets/q-narrow.png` are browser screenshots of the shipped exhibit's actual `qplot` canvas, using the full window and the 1522–1554 cm⁻¹ button respectively. No scientific data or plot pixels were redrawn.
- The bundled Inter font retains its OFL license in `assets/Inter-OFL.txt`. Other source-asset terms remain those in the repository's licensing notices.

## Validation

The delivered PDF was inspected with `pdfinfo`: 8 unencrypted pages, each 960 × 540 points, tagged PDF 1.4. All eight actual PDF pages were rendered with `pdftoppm` and visually reviewed: no content extends outside a page, diagrams and labels are legible, and both cases retain their intended visual weight. Seven PDF links were independently checked by the integrating reviewer. The slide-bound checks report no out-of-frame text and no browser errors.

The renderer uses a variable Inter font; Poppler emits font bounding-box warnings while rasterizing it. The actual rendered pages and extracted text were checked. Review images are retained locally in `preview/` and ignored by Git.
