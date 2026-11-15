/* Buildless, local-only human workspace. Drawing coordinates always use page space. */
"use strict";
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { tasks: [], task: null, evidence: [], mode: "pan", scale: 1, fit: 1,
  x: 0, y: 0, loaded: false, draft: null, drag: null, pointers: new Map(), request: 0,
  view: "overview", results: null, replayRequest: 0, toastTimer: null };
const families = { area: "Room area", room_area: "Room area", skirting: "Skirting & perimeter",
  openings: "Doors & windows", slab: "Slab takeoff", piping: "Piping & equipment" };
const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nice = (value) => families[value] || String(value || "").replace(/[_-]/g, " ");
const round = (value) => Math.round(value * 100) / 100;
const unitLabel = (value) => ({ m2: "m²", ft2: "ft²" }[value] || value || "");
function safeLink(value) { try { const url = new URL(value, location.origin); return ["https:", "http:"].includes(url.protocol) ? url.href : "#"; } catch { return "#"; } }
function toast(message) { $("#toast").textContent = message; $("#toast").hidden = false; clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 4200); }
async function api(path, options) { const response = await fetch(path, options); let data; try { data = await response.json(); } catch { throw new Error("The server returned an unreadable response. Please try again."); } if (!response.ok) throw new Error(data.error || data.detail || `Request failed (${response.status}).`); return data; }
const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

function showView(view, updateHash = true) {
  if (!["overview", "tour", "cavity", "workspace", "results"].includes(view)) view = "overview";
  state.view = view; document.body.dataset.currentView = view;
  if (view !== "results") replayPlayer.stop();
  $$(".view").forEach((element) => element.classList.toggle("active", element.id === `${view}-view`));
  $$(".nav-link").forEach((element) => element.classList.toggle("active", (element.dataset.view === view || (view === "workspace" && element.dataset.view === "tour"))));
  if (updateHash) history.replaceState(null, "", `#${view}${view === "workspace" && state.task ? `/${state.task.id}` : ""}`);
  if (view === "workspace") requestAnimationFrame(fitDrawing);
  if (view === "results") loadResults();
}
function mobilePanel(panel) {
  ["drawing", "answer"].forEach((name) => {
    const selected = name === panel;
    $(`#${name}-panel`).classList.toggle("mobile-active", selected);
    $(`#${name}-tab`).classList.toggle("active", selected);
    $(`#${name}-tab`).setAttribute("aria-selected", selected);
  });
  if (panel === "drawing") requestAnimationFrame(fitDrawing);
}
function renderCatalog() {
  const term = $("#task-search").value.trim().toLowerCase();
  const family = $("#family-filter").value; const condition = $("#condition-filter").value;
  const tasks = state.tasks.filter((task) => (!family || task.family === family) && (!condition || task.condition === condition) && `${task.title} ${task.question} ${task.id} ${nice(task.family)}`.toLowerCase().includes(term));
  $("#catalog-count").textContent = `${tasks.length} / ${state.tasks.length} TASKS`;
  $("#task-grid").innerHTML = tasks.length ? tasks.map((task) => `<article class="task-card"><div class="card-drawing"><img src="/api/tasks/${encodeURIComponent(task.id)}/image" alt="" loading="lazy"><span class="card-condition">${escapeHTML(task.condition)}</span><span class="card-number">${escapeHTML(task.id)}</span></div><div class="card-body"><div class="card-family">${escapeHTML(nice(task.family))}${task.trap ? '<span>JUDGMENT TEST</span>' : ""}</div><h3>${escapeHTML(task.title)}</h3><p>${escapeHTML(task.question)}</p><div class="card-footer"><span>${escapeHTML(task.difficulty)} · ${escapeHTML(task.split)}</span><button class="card-open" data-task="${escapeHTML(task.id)}" aria-label="Open ${escapeHTML(task.title)}, ${escapeHTML(task.condition)}">Open task</button></div></div></article>`).join("") : '<div class="empty-state"><h2>No matching drawings.</h2><p>Try another family, drawing condition, or search term.</p></div>';
}
async function loadCatalog() {
  try {
    state.tasks = await api("/api/tasks");
    $("#task-count").textContent = state.tasks.length;
    $("#family-count").textContent = new Set(state.tasks.map((t) => t.family)).size;
    $("#condition-count").textContent = new Set(state.tasks.map((t) => t.condition)).size;
    for (const [id, key] of [["family-filter", "family"], ["condition-filter", "condition"]]) {
      [...new Set(state.tasks.map((t) => t[key]))].sort().forEach((value) => { const option = new Option(nice(value), value); $(`#${id}`).add(option); });
    }
    state.tasks.forEach((task) => $("#task-select").add(new Option(`${task.title} · ${task.condition}`, task.id)));
    if (state.tasks.length) {
      $("#hero-image").setAttribute("href", "/api/tasks/bp-01-clean/image");
      $("#hero-placeholder").hidden = true;
    }
    renderCatalog();
    const [route, id] = location.hash.slice(1).split("/");
    if (id && state.tasks.some((task) => task.id === id)) await selectTask(id);
    else if (route === "workspace" && state.tasks.length) await selectTask(CASE_TASK);
    else if (route === "tour") await startTour(Number(id || 1) - 1);
    else if (route) showView(route, false);
  } catch (error) {
    $("#task-grid").innerHTML = `<div class="empty-state"><h2>Catalogue unavailable.</h2><p>${escapeHTML(error.message)}</p><button class="button secondary" id="retry-catalog">Try again</button></div>`;
    $("#retry-catalog").onclick = loadCatalog;
    $("#hero-placeholder").textContent = "The drawing catalogue is unavailable.";
  }
}
async function selectTask(id) {
  const task = state.tasks.find((item) => item.id === id); if (!task) return;
  const request = ++state.request; state.task = task; state.loaded = false; state.evidence = []; state.draft = null;
  $("#task-select").value = id;
  $("#task-title").textContent = task.title;
  $("#workspace-kicker").textContent = `${nice(task.family).toUpperCase()} / ${id.toUpperCase()}`;
  $("#task-question").textContent = task.question;
  $("#task-meta").innerHTML = [task.condition, task.difficulty, `${task.split} split`].map((v) => `<span class="meta-chip">${escapeHTML(v)}</span>`).join("") + (task.trap ? '<span class="meta-chip trap">Judgment test</span>' : "");
  $("#answer-form").reset(); $("#answer-value").disabled = false; $("#answer-confidence").value = 80; $("#confidence-output").textContent = "80%";
  $("#answer-unit").value = ["area", "room_area", "slab"].includes(task.family) ? "m2" : ["skirting"].includes(task.family) ? "m" : "count";
  $("#score-result").hidden = true; $("#solution-result").hidden = true; $("#reveal-solution").disabled = true; $("#submit-answer").disabled = true;
  $("#reveal-solution").textContent = "Reveal reference solution ↗";
  $("#drawing-message").textContent = "Loading source drawing…"; $("#drawing-message").hidden = false;
  $("#drawing-world").style.visibility = "hidden";
  $("#download-drawing").href = `/api/tasks/${encodeURIComponent(id)}/drawing`;
  const page = task.pages?.[0];
  $("#page-space").textContent = page ? `${round(page.width)} × ${round(page.height)} ${page.space === "pdf_pt" ? "pt" : "px"}` : "";
  $("#source-note").innerHTML = `SOURCE: <a href="${escapeHTML(safeLink(task.source?.url))}" target="_blank" rel="noopener">${escapeHTML(task.source?.title || "Source drawing")} ↗</a> · <a href="${escapeHTML(safeLink(task.source?.license_url))}" target="_blank" rel="noopener">${escapeHTML(task.source?.license || "See source license")}</a>${task.condition === "scan" ? "<br>Synthetic scan condition. Original physical scale and page extent retained." : ""}`;
  $("#box-x1").value = page ? round(page.width / 4) : ""; $("#box-y1").value = page ? round(page.height / 4) : "";
  renderEvidence(); setMode("pan"); mobilePanel("drawing"); showView("workspace"); window.scrollTo({ top: 0, behavior: "instant" });
  if (!page?.width || !page?.height) { $("#drawing-message").textContent = "Canonical page geometry is unavailable for this task."; return; }
  const image = $("#drawing-image");
  image.alt = `${task.title} — ${task.condition} source drawing`;
  image.onload = () => {
    if (request !== state.request) return;
    state.loaded = true; $("#drawing-message").hidden = true; $("#drawing-world").style.visibility = "visible";
    $("#drawing-world").style.width = `${page.width}px`; $("#drawing-world").style.height = `${page.height}px`;
    $("#evidence-overlay").setAttribute("viewBox", `0 0 ${page.width} ${page.height}`);
    $("#submit-answer").disabled = false; fitDrawing();
  };
  image.onerror = () => { if (request === state.request) { $("#drawing-message").textContent = "The drawing preview could not load. Try selecting this task again, or open the original."; $("#submit-answer").disabled = false; } };
  image.src = `/api/tasks/${encodeURIComponent(id)}/image`;
}
function transformDrawing() {
  $("#drawing-world").style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
  $("#zoom-level").textContent = `${Math.round(state.scale / state.fit * 100)}%`;
}
function fitDrawing() {
  if (!state.loaded || !state.task) return;
  const stage = $("#drawing-stage"), page = state.task.pages[0];
  if (!stage.clientWidth || !stage.clientHeight) return;
  state.fit = Math.min((stage.clientWidth - 40) / page.width, (stage.clientHeight - 40) / page.height);
  state.scale = state.fit; state.x = (stage.clientWidth - page.width * state.scale) / 2; state.y = (stage.clientHeight - page.height * state.scale) / 2;
  transformDrawing();
}
function zoom(factor, clientX, clientY) {
  if (!state.loaded) return;
  const rect = $("#drawing-stage").getBoundingClientRect();
  const x = clientX == null ? rect.width / 2 : clientX - rect.left;
  const y = clientY == null ? rect.height / 2 : clientY - rect.top;
  const next = Math.max(state.fit * .5, Math.min(state.fit * 12, state.scale * factor));
  state.x = x - (x - state.x) * next / state.scale; state.y = y - (y - state.y) * next / state.scale;
  state.scale = next; transformDrawing();
}
function pagePoint(event, clamp = false) {
  const rect = $("#drawing-stage").getBoundingClientRect(); const page = state.task.pages[0];
  let x = (event.clientX - rect.left - state.x) / state.scale, y = (event.clientY - rect.top - state.y) / state.scale;
  if (clamp) { x = Math.max(0, Math.min(page.width, x)); y = Math.max(0, Math.min(page.height, y)); }
  return [x, y];
}
function setMode(mode) {
  state.mode = mode;
  $("#drawing-stage").classList.toggle("box-mode", mode === "box");
  ["pan", "box"].forEach((name) => { $(`#${name}-mode`).classList.toggle("active", mode === name); $(`#${name}-mode`).setAttribute("aria-pressed", mode === name); });
  $("#pointer-coords").textContent = mode === "box" ? "Drag a rectangle around the evidence" : "Drag to explore · scroll to zoom";
}
function renderEvidence() {
  $("#evidence-count").textContent = state.evidence.length;
  $("#evidence-tab-count").textContent = state.evidence.length ? `(${state.evidence.length})` : "";
  $("#evidence-list").innerHTML = state.evidence.length ? state.evidence.map((item, i) => `<div class="evidence-item"><span>${String(i + 1).padStart(2, "0")}</span><div>[${item.bbox.map(round).join(", ")}] ${escapeHTML(item.space)}${item.note ? `<small>${escapeHTML(item.note)}</small>` : ""}</div><button type="button" data-remove="${i}" aria-label="Remove evidence region ${i + 1}">×</button></div>`).join("") : '<p class="evidence-empty">No regions marked yet.</p>';
  renderOverlay();
}
function renderOverlay() {
  const boxes = [...state.evidence]; if (state.draft) boxes.push({ bbox: state.draft.bbox, draft: true });
  $("#evidence-overlay").innerHTML = boxes.map((item, i) => { const [x0, y0, x1, y1] = item.bbox;
    return `<rect class="evidence-rect${item.draft ? " draft" : ""}" x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}"/>${!item.draft ? `<text class="evidence-index" x="${x0 + 4 / state.scale}" y="${y0 + 17 / state.scale}" style="font-size:${12 / state.scale}px">${i + 1}</text>` : ""}`;
  }).join("");
}
function addBox(bbox) {
  if (!state.task) return;
  const page = state.task.pages[0]; const [x0, y0, x1, y1] = bbox;
  if (!bbox.every(Number.isFinite) || x0 < 0 || y0 < 0 || x1 > page.width || y1 > page.height || x1 <= x0 || y1 <= y0) { toast(`Use an in-page rectangle: 0–${round(page.width)} × 0–${round(page.height)} ${page.space}.`); return; }
  if (state.evidence.length >= 32) { toast("A submission can include at most 32 evidence regions."); return; }
  state.evidence.push({ page: 0, bbox: bbox.map(round), space: page.space, note: $("#evidence-note").value.trim() }); renderEvidence();
  toast(`Region ${state.evidence.length} added in original ${page.space === "pdf_pt" ? "PDF points" : "image pixels"}.`);
}
const stage = $("#drawing-stage");
stage.addEventListener("wheel", (event) => { if (!state.loaded) return; event.preventDefault(); zoom(Math.exp(-event.deltaY * .0015), event.clientX, event.clientY); renderOverlay(); }, { passive: false });
stage.addEventListener("pointerdown", (event) => {
  if (!state.loaded || (event.button !== 0 && event.pointerType === "mouse")) return;
  stage.setPointerCapture(event.pointerId); state.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (state.pointers.size === 2) { state.draft = null; state.drag = null; renderOverlay(); return; }
  if (state.mode === "box") {
    const start = pagePoint(event); const page = state.task.pages[0];
    if (start[0] < 0 || start[1] < 0 || start[0] > page.width || start[1] > page.height) return;
    state.draft = { start, bbox: [...start, ...start] };
  } else { state.drag = { x: event.clientX, y: event.clientY }; stage.classList.add("dragging"); }
});
stage.addEventListener("pointermove", (event) => {
  if (!state.loaded) return;
  const oldPoints = [...state.pointers.values()];
  if (state.pointers.has(event.pointerId)) state.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (state.pointers.size === 2 && oldPoints.length === 2) {
    const points = [...state.pointers.values()]; const distance = (p) => Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
    const before = distance(oldPoints), after = distance(points);
    if (before > 2) zoom(after / before, (points[0].x + points[1].x) / 2, (points[0].y + points[1].y) / 2);
    renderOverlay(); return;
  }
  const point = pagePoint(event, true); $("#pointer-coords").textContent = `${round(point[0])}, ${round(point[1])} ${state.task.pages[0].space}`;
  if (state.draft) { const [x, y] = state.draft.start; state.draft.bbox = [Math.min(x, point[0]), Math.min(y, point[1]), Math.max(x, point[0]), Math.max(y, point[1])]; renderOverlay(); }
  else if (state.drag) { state.x += event.clientX - state.drag.x; state.y += event.clientY - state.drag.y; state.drag = { x: event.clientX, y: event.clientY }; transformDrawing(); }
});
function finishPointer(event) {
  state.pointers.delete(event.pointerId);
  if (state.draft && event.type !== "pointercancel") {
    const box = state.draft.bbox; if ((box[2] - box[0]) * state.scale > 4 && (box[3] - box[1]) * state.scale > 4) addBox(box);
  }
  state.draft = null; state.drag = null; stage.classList.remove("dragging"); renderOverlay();
}
stage.addEventListener("pointerup", finishPointer); stage.addEventListener("pointercancel", finishPointer);
stage.addEventListener("keydown", (event) => {
  if (!state.loaded) return;
  if (["+", "=", "-", "0", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Escape", "b", "p"].includes(event.key)) event.preventDefault();
  if (["+", "="].includes(event.key)) zoom(1.3); if (event.key === "-") zoom(1 / 1.3); if (event.key === "0") fitDrawing();
  if (event.key === "b") setMode("box"); if (event.key === "p") setMode("pan");
  if (event.key === "Escape") { state.draft = null; state.drag = null; }
  if (event.key === "ArrowLeft") state.x += 35; if (event.key === "ArrowRight") state.x -= 35;
  if (event.key === "ArrowUp") state.y += 35; if (event.key === "ArrowDown") state.y -= 35;
  transformDrawing(); renderOverlay();
});
new ResizeObserver(() => { if (state.view === "workspace") fitDrawing(); }).observe(stage);

$("#answer-form").addEventListener("submit", async (event) => {
  event.preventDefault(); if (!state.task) return;
  const raw = $("#answer-value").value, abstain = $("#abstain").checked;
  if (!abstain && (raw.trim() === "" || !Number.isFinite(Number(raw)))) { toast("Enter a finite quantity, or choose the abstention option."); $("#answer-value").focus(); return; }
  const taskId = state.task.id; const button = $("#submit-answer"); button.disabled = true; button.textContent = "Verifying…";
  $("#score-result").hidden = true;
  const answer = { value: abstain ? null : Number(raw), unit: $("#answer-unit").value,
    confidence: Number($("#answer-confidence").value) / 100, evidence: state.evidence,
    assumptions: $("#answer-assumptions").value.split("\n").map((s) => s.trim()).filter(Boolean) };
  try {
    const score = await post(`/api/tasks/${encodeURIComponent(taskId)}/score`, answer);
    if (taskId !== state.task?.id) return;
    const labels = [["Value", "value", .75], ["Evidence", "evidence", .15], ["Calibration", "calibration", .1]];
    const result = $("#score-result"); result.hidden = false; result.classList.toggle("error-result", !score.valid);
    result.innerHTML = `<div class="score-head"><span>${score.valid ? "VERIFIER REWARD" : "INVALID SUBMISSION"}</span><strong>${round(score.reward * 100)}<small>%</small></strong></div>${labels.map(([label, key, max]) => { const value = Number(score.components?.[key] || 0); return `<div class="score-row"><span>${label}</span><div class="score-bar"><span style="width:${Math.max(0, Math.min(100, value / max * 100))}%"></span></div><b>${round(value * 100)}/${max * 100}</b></div>`; }).join("")}<p class="score-explanation">${score.evidence_mode === "structural" ? "Structural evidence: the verifier checks valid in-page regions. It does not establish semantic relevance." : "Annotated evidence: regions are matched to the reference geometry."} Evidence credit is gated by value accuracy.</p>${score.errors?.length ? `<p class="score-explanation">${score.errors.map(escapeHTML).join("<br>")}</p>` : ""}`;
    $("#reveal-solution").disabled = false; result.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) { toast(error.message); }
  finally { if (taskId === state.task?.id) { button.disabled = false; button.innerHTML = "Verify my takeoff <span>↗</span>"; } }
});
$("#reveal-solution").addEventListener("click", async () => {
  if (!state.task) return; const id = state.task.id; const button = $("#reveal-solution"); button.disabled = true;
  try { const solution = await post(`/api/tasks/${encodeURIComponent(id)}/solution`, { reveal: true }); if (id !== state.task?.id) return;
    $("#solution-result").hidden = false; $("#solution-result").innerHTML = `<div class="solution-card"><span class="tiny-label">REFERENCE QUANTITY · HUMAN REVEAL</span><strong>${escapeHTML(solution.value)} ${escapeHTML(unitLabel(solution.unit))}</strong><p>${solution.evidence?.length ? `${solution.evidence.length} reference evidence region(s).` : "No semantic evidence annotation; structural validation only."}</p>${solution.assumptions?.length ? `<p>${solution.assumptions.map(escapeHTML).join("<br>")}</p>` : ""}</div>`; button.textContent = "Reference solution revealed";
  } catch (error) { toast(error.message); if (id === state.task?.id) button.disabled = false; }
});

// The guided case reads the same saved bundles as the full replay player.
const CASE_TASK = 'bp-01-clean';
const CASE_RUNS = ['full-deepseek-bp-01-clean', 'full-kimi-bp-01-clean'];
let tourRequest = 0;
async function startTour(step = 0, focus = false) {
  const request = ++tourRequest;
  state.tourStep = Math.max(0, Math.min(3, Number(step) || 0));
  showView('tour');
  history.replaceState(null, '', `#tour/${state.tourStep + 1}`);
  $('.tour-progress').querySelectorAll('button').forEach((button) => {
    const active = Number(button.dataset.tourStep) === state.tourStep;
    button.setAttribute('aria-current', active ? 'step' : 'false');
  });
  $('#tour-prev').disabled = state.tourStep === 0;
  $('#tour-position').textContent = `${state.tourStep + 1} of 4`;
  $('#tour-next').textContent = ['See the AI’s decision →', 'Reveal the comparison →', 'See how it is scored →', 'Try this task yourself ↗'][state.tourStep];
  $('#tour-content').setAttribute('aria-busy', 'true');
  try {
    if (!state.tourData) state.tourData = await Promise.all(CASE_RUNS.map((id) => api(`/api/runs/${id}`)));
    // Only the visitor's explicit comparison action reveals the reference.
    if (state.tourStep >= 2 && !state.tourReference) state.tourReference = await post(`/api/tasks/${CASE_TASK}/solution`, { reveal: true });
    if (request !== tourRequest) return;
    renderTour();
    if (focus) $('#tour-story-title').focus({ preventScroll: true });
  } catch (error) {
    if (request === tourRequest) $('#tour-content').innerHTML = `<div class="empty-state"><h2>We couldn’t load this saved run.</h2><p>${escapeHTML(error.message)}</p><button class="button secondary" data-tour-step="${state.tourStep}">Try again</button></div>`;
  } finally { if (request === tourRequest) $('#tour-content').removeAttribute('aria-busy'); }
}
function caseDrawing(mode) {
  const deepseek = state.tourData[0].submission.evidence.find((box) => box.note === 'fitness room net area extents used');
  const reference = state.tourReference?.evidence?.[0];
  const rectangle = (box, cls) => box ? `<rect class="${cls}" x="${box.bbox[0]}" y="${box.bbox[1]}" width="${box.bbox[2] - box.bbox[0]}" height="${box.bbox[3] - box.bbox[1]}"/>` : '';
  return `<div class="tour-drawing"><div class="tour-drawing-label"><span>SOURCE DRAWING</span><span>Fitness room · school floor plan</span></div><svg viewBox="2180 2130 350 475" role="img" aria-label="Enlarged fitness room. ${mode === 'reference' ? 'Orange shows the DeepSeek measurement, blue shows the reference boundary.' : mode === 'decision' ? 'Orange shows the boundary DeepSeek used.' : 'The room to measure is outlined in blue.'}"><image href="/api/tasks/${CASE_TASK}/image" width="4096" height="2897"/>${mode === 'task' ? '<rect class="case-target" x="2284" y="2215" width="140" height="323"/>' : rectangle(deepseek, 'case-model')}${mode === 'reference' ? rectangle(reference, 'case-reference') : ''}</svg><div class="drawing-legend">${mode === 'task' ? '<span><i class="legend-target"></i>Room to inspect</span>' : '<span><i class="legend-model"></i>DeepSeek’s submitted region</span>'}${mode === 'reference' ? '<span><i class="legend-reference"></i>Reference inner-wall footprint</span>' : ''}</div></div>`;
}
function renderTour() {
  const [deepseek, kimi] = state.tourData;
  const e = escapeHTML;
  const quantity = (run) => `${e(run.submission.value)} <small>${e(unitLabel(run.submission.unit))}</small>`;
  const replayButton = (run, name, step = '') => `<button class="text-button" data-open-record="${e(run.run.id)}" ${step ? `data-record-step="${step}"` : ''}>Replay ${e(name)}’s saved run ↗</button>`;
  let html;
  if (state.tourStep === 0) {
    html = `<div class="tour-scene">${caseDrawing('task')}<div class="tour-story"><p class="eyebrow">1 / THE TASK</p><h2 id="tour-story-title" tabindex="-1">Measure this room.</h2><p class="tour-lead">Find the internal floor area of the fitness room.</p><p>The AI receives a real school floor plan. It must identify the room, choose its boundary, read the scale and submit an area with supporting evidence.</p><div class="tour-tools"><span>Inspect the image</span><span>Crop and zoom</span><span>Read dimensions</span><span>Calculate</span></div><p class="tour-note">This walkthrough follows two saved model runs on the same task. You can inspect the full recorded actions at the end.</p></div></div>`;
  } else if (state.tourStep === 1) {
    html = `<div class="tour-scene">${caseDrawing('decision')}<div class="tour-story"><p class="eyebrow">2 / THE DECISION</p><h2 id="tour-story-title" tabindex="-1">Which line is the wall?</h2><p class="tour-lead">DeepSeek measures from the upper line and reports ${quantity(deepseek)}.</p><p>In its saved reasoning, it treats the lower horizontal line as furniture or equipment. That choice makes the measured room longer.</p><blockquote>“Horizontal line at y~2245 within the cell treated as furniture/equipment, not a dividing wall.”<cite>DeepSeek · saved submission assumption</cite></blockquote><p>The orange region is the area it actually used. The next step compares that decision with the reference.</p>${replayButton(deepseek, 'DeepSeek', '27')}</div></div>`;
  } else if (state.tourStep === 2) {
    const ref = state.tourReference;
    const difference = (run) => ((run.submission.value / ref.value - 1) * 100).toFixed(1);
    html = `<div class="tour-scene">${caseDrawing('reference')}<div class="tour-story"><p class="eyebrow">3 / THE COMPARISON</p><h2 id="tour-story-title" tabindex="-1">The boundary matters.</h2><p class="tour-lead">The reference area is <strong>${e(ref.value)} ${e(unitLabel(ref.unit))}</strong>.</p><p>The blue region follows the inner-wall footprint. DeepSeek’s region reaches higher; Kimi’s answer is much closer to the reference.</p><div class="tour-answer-cards"><article><span>DeepSeek</span><strong>${quantity(deepseek)}</strong><small>+${difference(deepseek)}% from reference</small></article><article><span>Kimi</span><strong>${quantity(kimi)}</strong><small>${difference(kimi)}% from reference</small></article></div><p class="tour-note">An answer can look plausible while missing the room boundary. The source, submitted regions and scoring breakdown let you inspect the difference.</p></div></div>`;
  } else {
    const scoreCard = (run, name) => `<article class="tour-score-card"><div><span>${e(name)}</span><strong>${run.run.reward.toFixed(3)}<small> / 1 reward</small></strong></div>${[['Quantity', 'value', .75], ['Evidence', 'evidence', .15], ['Confidence', 'calibration', .1]].map(([label, key, max]) => `<div class="tour-component"><span>${label}</span><meter min="0" max="${max}" value="${run.score.components[key]}">${run.score.components[key]}</meter><small>${run.score.components[key].toFixed(3)} / ${max.toFixed(2)}</small></div>`).join('')}${replayButton(run, name)}</article>`;
    html = `<div class="tour-score-scene"><div class="tour-story"><p class="eyebrow">4 / THE SCORE</p><h2 id="tour-story-title" tabindex="-1">A number.<br>And the evidence behind it.</h2><p class="tour-lead">The same fixed verifier scores both submissions.</p><p>Quantity earns up to 0.75, drawing evidence up to 0.15, and confidence up to 0.10. Evidence credit depends on quantity accuracy.</p><p>Kimi gets full quantity credit on this task, but only partial evidence credit. A close answer still has room for better support.</p><div class="tour-final-actions"><button class="button primary" data-task="${CASE_TASK}">Try it yourself ↗</button><button class="text-button" data-view="results">Compare all results →</button></div><details class="tour-method"><summary>How to interpret this example</summary><p>These are two historical model runs, one per model on this task. They illustrate a specific difference, not performance across repeated trials. Reward combines quantity, evidence overlap and confidence; it is not a percentage of tasks solved. The reference is revealed here for the visitor, outside the evaluated agent’s workspace.</p></details></div><div class="tour-score-stack">${scoreCard(deepseek, 'DeepSeek')}${scoreCard(kimi, 'Kimi')}</div></div>`;
  }
  $('#tour-content').innerHTML = html;
}
function resultsOverview(result) {
  const realModels = ['kimi', 'deepseek'];
  const cards = realModels.map((name) => {
    const runs = result.runs.filter((run) => (run.model || run.agent || '').toLowerCase().includes(name));
    const unique = new Set(runs.map((run) => run.task_id)).size;
    const complete = runs.length === state.tasks.length && unique === state.tasks.length && runs.every((run) => Number.isFinite(run.reward));
    const mean = complete ? runs.reduce((sum, run) => sum + run.reward, 0) / runs.length : null;
    const title = name === 'kimi' ? 'Kimi' : 'DeepSeek';
    return `<article class="model-result"><div><span>${title}</span><strong>${mean === null ? '—' : mean.toFixed(3)}<small> / 1</small></strong></div><p>Mean reward · ${unique} drawing tasks</p><div class="model-mean-track"><span style="width:${mean === null ? 0 : mean * 100}%"></span></div><small>${complete ? 'One saved run per task' : 'Incomplete coverage; mean withheld'}</small></article>`;
  }).join('');
  return `<div class="results-overview"><div class="results-summary-copy"><p class="eyebrow">SAME DRAWINGS. SAME RULES.</p><h2>Performance you can inspect.</h2><p>Each model tackles all ${state.tasks.length} drawing tasks: rooms, wall perimeters, openings, slabs and piping, across clean images, vector plans and synthetic scans.</p><p>These are saved evaluation runs. The score rewards a correct quantity, useful drawing evidence and calibrated confidence.</p></div><div class="model-results">${cards}</div></div><section class="result-case"><div><p class="eyebrow">START WITH ONE EXAMPLE</p><h3>Two answers to the same room.</h3><p>DeepSeek: 29.1 m². Kimi: 26.4 m².<br>Follow the boundary decision and see the score.</p></div><div><button class="button primary" data-tour-step="0">Follow the guided case →</button><button class="text-button" data-open-record="full-deepseek-bp-01-clean" data-record-step="27">Replay DeepSeek’s decision ↗</button><button class="text-button" data-open-record="full-kimi-bp-01-clean">Replay Kimi’s run ↗</button></div></section><div class="result-context"><article><h3>Controls keep the score honest.</h3><p>The reference-writing control scores 1.000 and the no-action control scores 0.000. These are checks on the environment, not AI model results.</p></article><article><h3>Read the score in context.</h3><p>Reward is a combined score from 0 to 1, not a task success rate. This collection contains one run per model and task; it does not measure repeated-run variability or show a trained policy improvement.</p></article></div><div class="results-secondary"><a href="/science/">Explore the separate mathematical evaluation ↗</a><a href="/guide/">产品详解 · 中文手册 ↗</a></div>`;
}

function table(headers, rows) { return `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th scope="col">${escapeHTML(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`; }
const numeric = (value, suffix = "") => value == null || !Number.isFinite(Number(value)) ? "—" : `${round(Number(value))}${suffix}`;
async function loadResults() {
  const button = $("#refresh-results"); button.disabled = true;
  try {
    const result = await api("/api/results"); state.results = result;
    let html = "";
    if (!result.runs.length && !result.summary.length) {
      html = `<div class="empty-state"><span class="empty-symbol" aria-hidden="true">⌑</span><p class="eyebrow">${result.status === "pending" ? "AWAITING RECORDED RUNS" : "RESULTS UNAVAILABLE"}</p><h2>The ledger starts with evidence.</h2><p>${escapeHTML(result.message || "No recorded model runs are available yet. Rewards, costs, and trajectories appear here after real evaluation runs are exported.")}</p></div>`;
    } else {
      html = resultsOverview(result) + `<details class="full-results"><summary>Inspect the complete run records</summary><p class="results-note">Export status: ${escapeHTML(result.status)}. ${escapeHTML(result.message || "Missing costs are shown as —; they are not estimated. Infrastructure errors remain visible.")}</p>`;
      if (result.summary.length) html += "<h2>By family & condition</h2>" + table(["Model / agent", "Family", "Condition", "Tasks", "Mean reward", "Completed", "Failed", "Cost"], result.summary.map((row) => `<tr><td>${escapeHTML(row.model || row.agent)}</td><td>${escapeHTML(nice(row.family))}</td><td>${escapeHTML(row.condition)}</td><td>${numeric(row.n)}</td><td>${numeric(row.mean_reward == null ? null : row.mean_reward * 100, "%")}</td><td>${numeric(row.completed)}</td><td>${numeric(row.failed)}</td><td>${row.cost_usd == null ? "—" : `$${numeric(row.cost_usd)}`}</td></tr>`));
      if (result.runs.length) html += "<h2>Recorded trajectories</h2>" + table(["Model / agent", "Task", "Reward", "Status", "Duration", "Replay"], result.runs.map((run) => `<tr><td>${escapeHTML(run.model || run.agent)}</td><td>${escapeHTML(run.task_id)}</td><td>${numeric(run.reward == null ? null : run.reward * 100, "%")}</td><td>${escapeHTML(run.status)}</td><td>${numeric(run.duration_sec, "s")}</td><td>${run.trajectory_url ? `<button class="text-button" data-run="${escapeHTML(run.id)}">Inspect ↗</button>` : "Not exported"}</td></tr>`));
    }
    if (result.runs.length || result.summary.length) html += "</details>";
    $("#results-content").innerHTML = html;
  } catch (error) { $("#results-content").innerHTML = `<div class="empty-state"><h2>Could not load results.</h2><p>${escapeHTML(error.message)}</p><p>Use Refresh results to try again.</p></div>`; }
  finally { button.disabled = false; }
}
async function replay(id, step) {
  const request = ++state.replayRequest;
  replayPlayer.clear();
  $("#replay-panel").hidden = false; $("#replay-title").textContent = "Saved model run"; $("#replay-content").textContent = "Loading exported trajectory…";
  try {
    const data = await api(`/api/runs/${encodeURIComponent(id)}`);
    if (request !== state.replayRequest || $("#replay-panel").hidden) return;
    replayPlayer.mount(data, state.results?.runs?.find((run) => run.id === id) || { id });
    if (Number.isInteger(step)) replayPlayer.seek(step);
    $("#replay-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { if (request === state.replayRequest && !$("#replay-panel").hidden) $("#replay-content").textContent = error.message; }
}
document.addEventListener("click", (event) => {
  const nav = event.target.closest("[data-view]"); if (nav) { if (nav.dataset.view === "tour") startTour(); else if (nav.dataset.view === "workspace" && !state.task && state.tasks.length) selectTask(CASE_TASK); else showView(nav.dataset.view); window.scrollTo({ top: 0, behavior: "instant" }); }
  const guided = event.target.closest("[data-tour-step]"); if (guided) { startTour(guided.dataset.tourStep, true); window.scrollTo({ top: 0, behavior: "instant" }); }
  const record = event.target.closest("[data-open-record]"); if (record) { showView("results"); replay(record.dataset.openRecord, record.hasAttribute("data-record-step") ? Number(record.dataset.recordStep) : undefined); }
  const task = event.target.closest("[data-task]"); if (task) selectTask(task.dataset.task);
  const remove = event.target.closest("[data-remove]"); if (remove) { state.evidence.splice(Number(remove.dataset.remove), 1); renderEvidence(); }
  const run = event.target.closest("[data-run]"); if (run) replay(run.dataset.run);
});
$("#start-work").onclick = () => { if (state.tasks.length) selectTask(CASE_TASK); else { $("#task-grid").scrollIntoView({ behavior: "smooth" }); toast("The task catalogue is not available yet."); } };
$("#start-tour").onclick = () => { startTour(); window.scrollTo({ top: 0, behavior: "instant" }); };
$("#tour-prev").onclick = () => startTour(state.tourStep - 1, true);
$("#tour-next").onclick = () => { if (state.tourStep === 3) selectTask(CASE_TASK); else startTour(state.tourStep + 1, true); };
$("#browse-tasks").onclick = () => { $("#task-library").hidden = false; $("#task-library").scrollIntoView({ behavior: "smooth" }); $("#task-search").focus({ preventScroll: true }); };
$("#task-select").onchange = (event) => selectTask(event.target.value);
["task-search", "family-filter", "condition-filter"].forEach((id) => $(`#${id}`).addEventListener(id === "task-search" ? "input" : "change", renderCatalog));
$("#zoom-in").onclick = () => { zoom(1.3); renderOverlay(); }; $("#zoom-out").onclick = () => { zoom(1 / 1.3); renderOverlay(); }; $("#fit-drawing").onclick = fitDrawing;
$("#pan-mode").onclick = () => setMode("pan"); $("#box-mode").onclick = () => setMode("box");
$("#add-evidence").onclick = () => { mobilePanel("drawing"); setMode("box"); stage.focus({ preventScroll: true }); toast("Drag a rectangle around relevant dimensions or geometry. Keyboard users can enter coordinates in the answer panel."); };
$("#add-coordinate-box").onclick = () => { const ids = ["box-x0", "box-y0", "box-x1", "box-y1"]; if (ids.some((id) => $(`#${id}`).value.trim() === "")) { toast("Enter all four rectangle coordinates."); return; } addBox(ids.map((id) => Number($(`#${id}`).value))); };
$("#answer-confidence").oninput = (event) => { $("#confidence-output").textContent = `${event.target.value}%`; };
$("#abstain").onchange = (event) => { $("#answer-value").disabled = event.target.checked; };
$("#drawing-tab").onclick = () => mobilePanel("drawing"); $("#answer-tab").onclick = () => mobilePanel("answer");
$$(".mobile-tabs button").forEach((button) => button.addEventListener("keydown", (event) => { if (["ArrowLeft", "ArrowRight"].includes(event.key)) { event.preventDefault(); const target = button.id === "drawing-tab" ? "answer" : "drawing"; mobilePanel(target); $(`#${target}-tab`).focus(); } }));
$("#refresh-results").onclick = loadResults; $("#close-replay").onclick = () => { ++state.replayRequest; replayPlayer.clear(); $("#replay-panel").hidden = true; };
window.addEventListener("hashchange", () => { const [view, id] = location.hash.slice(1).split("/"); if (view === "tour") startTour(Number(id || 1) - 1); else if (view === "workspace" && id && id !== state.task?.id) selectTask(id); else showView(view || "overview", false); });
const replayPlayer = new ReplayPlayer({ root: $("#replay-content"), tasks: () => state.tasks,
  openTask: selectTask, score: (id, answer) => post(`/api/tasks/${encodeURIComponent(id)}/score`, answer), escape: escapeHTML });
if (location.hash.split("/")[0] === "#cavity") showView("cavity", false);
loadCatalog();
