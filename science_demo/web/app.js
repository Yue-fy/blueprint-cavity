/* Private saved-data explorer. Reference material arrives only on explicit POST. */
"use strict";
const $ = (selector) => document.querySelector(selector);
const state = { cases: [], current: null, revealed: null, generation: 0 };
const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
const number = (value) => Number(value).toLocaleString("en", { maximumSignificantDigits: 6 });
const mainNumber = (value) => String(Number(Number(value).toPrecision(10)));
const percent = (value) => `${number(100 * value)}%`;
async function api(path, options) {
  const response = await fetch(`/science/api${path}`, options);
  let data; try { data = await response.json(); } catch { throw new Error("The server returned an unreadable response."); }
  if (!response.ok) throw new Error(data.error || "The saved validation is unavailable.");
  return data;
}
function selectCase() {
  ++state.generation;
  state.current = state.cases.find((item) => item.id === $("#case-select").value);
  state.revealed = null;
  $("#results").hidden = true; $("#reveal-gate").hidden = false; $("#error").hidden = true;
  $("#reveal").disabled = false; $("#reveal").textContent = "Reveal saved validation ↗";
  $("#grid-select").value = "1024"; $("#view-select").value = "ratio";
  const item = state.current;
  $("#parameters").innerHTML = Object.entries(item.parameters).map(([key, value]) => `<span>${escapeHTML(key)} <b>${escapeHTML(value)}</b></span>`).join("");
  $("#case-kind").textContent = item.control_nondiscriminating ? "A = 0 CONTROL" : "NONZERO A";
  $("#domain-value").textContent = `Saved sufficient bound B = ${mainNumber(item.domain_bound)} < 1 · only this validated parameter set`;
}
async function reveal() {
  const generation = state.generation, id = state.current.id;
  $("#reveal").disabled = true; $("#reveal").textContent = "Loading saved validation…"; $("#error").hidden = true;
  try {
    const data = await api(`/cases/${encodeURIComponent(id)}/reveal`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reveal: true }) });
    if (generation !== state.generation) return;
    state.revealed = data;
    const item = data.case;
    $("#reference-formula").textContent = data.explanation.reference_formula;
    $("#historical-formula").textContent = data.explanation.historical_formula;
    $("#reference-value").textContent = mainNumber(item.reference.value);
    $("#reference-fraction").textContent = `Exact rational: ${item.reference.numerator} / ${item.reference.denominator}`;
    $("#historical-value").textContent = mainNumber(item.historical_wrong);
    $("#historical-discrepancy").textContent = `${percent(item.historical_relative_error)} discrepancy from the reference`;
    $("#control-note").textContent = item.control_nondiscriminating ? "A = 0 control: agreement is nondiscriminating. The two expressions coincide here; this is not a failed trap." : "This nonzero-A case discriminates the alternatives: their saved reference values differ.";
    $("#mechanism").textContent = data.explanation.mechanism;
    $("#proof").textContent = data.proof;
    $("#raw").textContent = JSON.stringify(item, null, 2);
    $("#saved-limitations").innerHTML = data.limitations.map((text) => `<li>${escapeHTML(text)}</li>`).join("");
    $("#provenance").innerHTML = `<p>${escapeHTML(data.method.coefficient_extraction)}</p><p>${escapeHTML(data.method.normalization)}</p><p>${escapeHTML(data.method.independence)}</p><p>Recorded M = ${escapeHTML(item.grid_size)} radius: ${escapeHTML(item.radius)}. Compared M = ${escapeHTML(item.grid_sensitivity.compared_grid_size)} radius: ${escapeHTML(item.grid_sensitivity.compared_radius)}.</p><p>Maximum imaginary ratio: ${escapeHTML(item.max_imaginary_ratio)}. Roundoff diagnostics are scales, not rigorous bounds.</p><dl>${Object.entries(data.source_sha256).map(([name, hash]) => `<dt>${escapeHTML(name)} · SHA-256</dt><dd>${escapeHTML(hash)}</dd>`).join("")}</dl>`;
    renderPlot();
    $("#results-heading").textContent = `Saved validation loaded · ${id.toUpperCase()}`;
    $("#results").hidden = false; $("#reveal-gate").hidden = true;
    $("#results-heading").focus();
  } catch (error) {
    if (generation !== state.generation) return;
    state.revealed = null; $("#results").hidden = true; $("#reveal-gate").hidden = false;
    $("#error").textContent = error.message; $("#error").hidden = false;
    $("#reveal").disabled = false; $("#reveal").textContent = "Reveal saved validation ↗";
  }
}
function renderPlot() {
  if (!state.revealed) return;
  const item = state.revealed.case, reference = item.reference.value;
  const grid = Number($("#grid-select").value), errorView = $("#view-select").value === "error";
  const selected = grid === item.grid_size ? item.ratios : item.grid_sensitivity.compared_ratios;
  const other = grid === item.grid_size ? item.grid_sensitivity.compared_ratios : item.ratios;
  const otherGrid = grid === item.grid_size ? item.grid_sensitivity.compared_grid_size : item.grid_size;
  const convert = (ratio) => errorView ? ratio / reference - 1 : ratio;
  const values = [...selected, ...other].map(convert), baseline = errorView ? 0 : reference;
  const low = Math.min(...values, baseline), high = Math.max(...values, baseline), margin = (high - low || Math.abs(high) * .01 || 1) * .18;
  const bottom = low - margin, top = high + margin;
  const compact = window.matchMedia("(max-width:760px)").matches;
  const width = compact ? 360 : 650, height = compact ? 280 : 325;
  const left = 105, right = compact ? 338 : 585, base = compact ? 230 : 275;
  const x = (index) => left + index * (right - left - 25) / 2;
  const y = (value) => base - (value - bottom) / (top - bottom) * (compact ? 185 : 225);
  const label = (value) => errorView ? percent(value) : number(value);
  const points = (series) => series.map((ratio, index) => `${x(index)},${y(convert(ratio))}`).join(" ");
  const ticks = Array.from({ length: 5 }, (_, index) => bottom + (top - bottom) * index / 4);
  $("#plot").innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Saved coefficient measurements at indices 80,100,120"><title>${errorView ? "Relative error" : "Coefficient ratio"} for ${escapeHTML(item.id)}, selected grid ${grid}</title>${ticks.map((tick) => `<line class="grid-line" x1="${left}" x2="${right}" y1="${y(tick)}" y2="${y(tick)}"/><text class="tick" x="${left - 14}" y="${y(tick) + 4}" text-anchor="end">${escapeHTML(label(tick))}</text>`).join("")}<line class="reference-line" x1="${left}" x2="${right}" y1="${y(baseline)}" y2="${y(baseline)}"/><polyline class="other-series" points="${points(other)}"/><polyline class="selected-series" points="${points(selected)}"/>${other.map((ratio, index) => `<circle class="other-point" cx="${x(index)}" cy="${y(convert(ratio))}" r="4"/>`).join("")}${selected.map((ratio, index) => `<circle tabindex="0" role="button" class="data-point" data-index="${index}" cx="${x(index)}" cy="${y(convert(ratio))}" r="7" aria-label="Index ${item.indices[index]}, grid ${grid}, ratio ${ratio}"><title>i = ${item.indices[index]} · ${ratio}</title></circle>`).join("")}${item.indices.map((index, offset) => `<text class="tick" x="${x(offset)}" y="${height - 24}" text-anchor="middle">${index}</text>`).join("")}<text class="axis-label" x="${width / 2}" y="${height - 4}" text-anchor="middle">Coefficient index i</text></svg><div class="legend"><span class="selected-key">M = ${grid} selected</span><span class="other-key">M = ${otherGrid} comparison</span><span class="reference-key">Independent reference</span></div>`;
  const detail = (event) => { const point = event.target.closest(".data-point"); if (!point) return; const index = Number(point.dataset.index); $("#point-detail").textContent = `i = ${item.indices[index]} · M = ${grid} · ratio ${selected[index]} · relative error ${selected[index] / reference - 1}`; };
  $("#plot").querySelectorAll(".data-point").forEach((point) => { point.onfocus = detail; });
  $("#plot").onpointerover = detail;
  $("#plot").onkeydown = (event) => {
    const point = event.target.closest(".data-point"); if (!point) return;
    if (["ArrowLeft", "ArrowRight"].includes(event.key)) { event.preventDefault(); const index = Math.max(0, Math.min(2, Number(point.dataset.index) + (event.key === "ArrowRight" ? 1 : -1))); $("#plot").querySelector(`[data-index="${index}"]`).focus(); }
  };
  $("#point-detail").textContent = "Focus or hover a point for its recorded value. Arrow keys move between points.";
  $("#plot-caption").textContent = `${errorView ? "Relative error = recorded ratio / independent reference − 1." : "Ratio view is zoomed near the independent reference; the historical alternative is compared above."} Points are saved measurements; connecting lines guide the eye and are not additional samples.`;
  $("#measurements tbody").innerHTML = item.indices.map((index, offset) => `<tr><th scope="row">${index}</th><td>${selected[offset]}</td><td>${selected[offset] / reference - 1}</td><td>${other[offset]}</td></tr>`).join("");
}
$("#case-select").onchange = selectCase; $("#reveal").onclick = reveal;
$("#grid-select").onchange = renderPlot; $("#view-select").onchange = renderPlot;
window.addEventListener("resize", renderPlot);
api("/cases").then((data) => {
  state.cases = data.cases;
  $("#case-select").innerHTML = data.cases.map((item) => `<option value="${escapeHTML(item.id)}">${escapeHTML(item.id.toUpperCase())}${item.control_nondiscriminating ? " · A = 0 control" : ""}</option>`).join("");
  $("#loading").hidden = true; $("#explorer").hidden = false; selectCase();
}).catch((error) => { $("#loading").textContent = error.message; });

function renderTrials(data) {
  const loading = $("#trial-loading");
  $("#trial-jobs").replaceChildren();
  $("#trial-export").hidden = true;
  if (!data.available) {
    loading.hidden = false;
    loading.textContent = "No saved model trial export yet. Numerical validation is available below.";
    return;
  }
  loading.hidden = true;
  $("#trial-export").hidden = false;
  $("#trial-export").textContent = `Saved export: ${data.exported_at} · refresh saved results for a newer snapshot.`;
  const reward = (row) => row.reward === null ? (row.status === "pending" ? "Pending" : "Not graded") : String(row.reward);
  const cost = (value) => value === null ? "Unknown" : `$${value}`;
  const duration = (value) => value === null ? "Unknown" : `${value} s`;
  $("#trial-jobs").innerHTML = data.summary.map((job) => {
    const rows = data.runs.filter((row) => row.job === job.job);
    const stateLabel = job.pending ? `Partial saved run · ${job.pending} pending` : "All tasks finished";
    const warning = job.warnings ? `${job.warnings} graded with warning. Official rewards are retained, including zero.` : "No graded warnings recorded.";
    return `<article class="trial-job"><div class="trial-job-heading"><div><h3>${escapeHTML(job.model)}</h3><p class="trial-job-id">Job: ${escapeHTML(job.job)}</p></div><span class="trial-state">${stateLabel}</span></div><dl class="trial-metrics"><div><dt>Mean official reward</dt><dd class="trial-mean">${job.mean_reward === null ? "Pending" : job.mean_reward}</dd></div><div><dt>Graded / planned</dt><dd class="trial-graded">${job.graded} / ${job.planned}</dd></div><div><dt>Failed / missing</dt><dd>${job.failed} / ${job.missing}</dd></div><div><dt>API cost (USD)</dt><dd class="trial-cost">${cost(job.cost_usd)}</dd></div></dl><p class="trial-warning">${warning}</p><div class="trial-tasks">${rows.map((row) => `<details class="trial-task" data-task="${escapeHTML(row.task_id)}"><summary><span>${escapeHTML(row.task_id)}</span><span class="task-status">${escapeHTML(row.status.replaceAll("_", " "))}</span><span class="task-summary-reward">Reward ${reward(row)}</span></summary><dl><div><dt>Official reward</dt><dd class="task-reward">${reward(row)}</dd></div><div><dt>Duration</dt><dd class="task-duration">${duration(row.duration_sec)}</dd></div><div><dt>API cost (USD)</dt><dd>${cost(row.cost_usd)}</dd></div><div><dt>Error type</dt><dd>${escapeHTML(row.error_type || "None recorded")}</dd></div></dl></details>`).join("")}</div></article>`;
  }).join("");
}
async function loadTrials() {
  $("#trial-refresh").disabled = true;
  $("#trial-refresh").textContent = "Refreshing saved results…";
  $("#model-trials").setAttribute("aria-busy", "true");
  try {
    renderTrials(await api("/results"));
  } catch {
    $("#trial-loading").hidden = false;
    $("#trial-loading").textContent = $("#trial-jobs").childElementCount
      ? "Refresh unavailable. Showing the previous saved snapshot. Try refreshing again."
      : "Saved model trial results are unavailable. Numerical validation is available below. Try refreshing again.";
  } finally {
    $("#trial-refresh").disabled = false;
    $("#trial-refresh").textContent = "Refresh saved results";
    $("#model-trials").setAttribute("aria-busy", "false");
  }
}
$("#trial-refresh").onclick = loadTrials;
loadTrials();
