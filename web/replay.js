/* Recorded events only. No inference, reference fetching, or answer editing. */
"use strict";
window.ReplayPlayer = class ReplayPlayer {
  constructor({ root, tasks, openTask, score, escape }) {
    Object.assign(this, { root, tasks, openTask, score, escape });
    this.generation = 0;
  }
  stop() {
    clearInterval(this.timer); this.timer = null;
    const button = this.query("#replay-play");
    if (button) { button.textContent = "Play ▶"; button.setAttribute("aria-label", "Play recorded steps"); }
  }
  clear() { this.stop(); this.generation++; }
  text(value) { return typeof value === "string" ? value : JSON.stringify(value, null, 2) ?? ""; }
  block(label, value, raw = false) {
    const content = this.text(value), e = this.escape;
    if (!content) return "";
    if (raw) return `<details class="replay-details"><summary>${e(label)}</summary><pre>${e(content)}</pre></details>`;
    if (content.length > 1000) return `<section class="replay-block"><h4>${e(label)}</h4><pre>${e(content.slice(0, 700))}…</pre><details class="replay-details"><summary>Read full ${e(label.toLowerCase())} (${content.length.toLocaleString()} characters)</summary><pre>${e(content)}</pre></details></section>`;
    return `<section class="replay-block"><h4>${e(label)}</h4><pre>${e(content)}</pre></section>`;
  }
  mount(data, ledger = {}) {
    this.clear(); this.data = data; this.index = 0;
    this.timelineStart = null; this.timelineActive = null;
    this.bundle = data?.format === "blueprint-replay-v1";
    this.run = this.bundle ? { ...ledger, ...data.run } : ledger;
    this.trajectory = this.bundle ? data.trajectory : data;
    const source = this.trajectory;
    this.steps = Array.isArray(source) ? source : [source?.steps, source?.events, source?.messages, source?.trajectory].find(Array.isArray) || [];
    this.task = this.tasks().find((task) => task.id === this.run.task_id);
    this.answer = this.bundle ? data.submission : null;
    const reason = this.answerIssue();
    const e = this.escape, run = this.run, score = this.bundle ? data.score : null;
    const model = run.model || run.agent || source?.agent?.model_name || "Model unavailable";
    const warnings = [run.warning, run.warnings, run.error_type, data?.warning, data?.warnings, data?.submission_error].flat().filter(Boolean);
    this.root.innerHTML = `<div class="replay-run-header"><div><p class="eyebrow">RECORDED MODEL WORK</p><h3>${e(model)}</h3><p>${e(run.task_id || "Task metadata unavailable")} · ${e(run.status || "Status unavailable")}</p></div><div class="replay-reward"><span>OFFICIAL REWARD</span><strong>${typeof run.reward === "number" && Number.isFinite(run.reward) ? `${e((run.reward * 100).toFixed(2))}%` : "—"}</strong>${run.reward == null ? "<small>Official reward unavailable</small>" : ""}</div></div>
      ${warnings.map((warning) => `<p class="replay-warning">${e(this.text(warning))}</p>`).join("")}
      <p class="replay-caption">Playback of exported events. No new model run is started.</p>
      <div class="replay-player"><div class="replay-controls"><button type="button" id="replay-prev" aria-label="Previous recorded step">← Previous</button><button type="button" id="replay-play" aria-label="Play recorded steps">Play ▶</button><button type="button" id="replay-next" aria-label="Next recorded step">Next →</button><output id="replay-position" aria-live="polite"></output></div><label class="sr-only" for="replay-progress">Recorded step</label><input id="replay-progress" type="range" min="0" max="${Math.max(0, this.steps.length - 1)}" value="0" step="1"><p id="replay-window" class="replay-caption" hidden></p><div class="replay-body"><nav class="replay-timeline" aria-label="Recorded steps"></nav><article id="replay-step" tabindex="0" aria-label="Current recorded step"></article></div></div>
      <section class="replay-saved"><div class="replay-saved-heading"><div><p class="eyebrow">SAVED SCORING EVIDENCE</p><h3>The submitted answer</h3></div><button type="button" id="replay-open-source" class="button secondary" ${this.task ? "" : "disabled"}>Open source task ↗</button></div>
      ${this.answer && typeof this.answer === "object" ? `<p class="replay-answer-summary">${e(this.answer.value === null ? "Abstained" : this.text(this.answer.value))} ${e(this.answer.unit)} <span>Confidence ${e(this.text(this.answer.confidence))}</span></p>` : ""}
      <p class="replay-caption">${e(reason || "The recheck sends the saved JSON unchanged to the current verifier. It is separate from the recorded official reward.")}</p><div class="replay-actions"><button type="button" id="replay-evidence" class="button secondary" ${this.task && this.validBoxes().length ? "" : "disabled"}>Show saved evidence on source</button><button type="button" id="replay-recheck" class="button primary" ${reason ? "disabled" : ""}>Recheck saved answer</button></div><div id="replay-source" hidden></div><div id="replay-recheck-result" role="status"></div>
      ${score && typeof score === "object" ? `<div class="replay-recorded-score"><h4>Recorded verifier breakdown</h4><p>${run.reward == null ? "A score file exists; the official trial reward is still unavailable. " : ""}Verifier reward: ${e(this.text(score.reward ?? "unavailable"))} · ${score.valid === true ? "Valid submission" : score.valid === false ? "Invalid submission" : "Validity unavailable"}</p>${score.components && typeof score.components === "object" ? `<dl>${Object.entries(score.components).map(([key, value]) => `<div><dt>${e(key)}</dt><dd>${e(this.text(value))}</dd></div>`).join("")}</dl>` : ""}${this.block("Recorded verifier details", score, true)}</div>` : '<p class="replay-caption">Recorded scoring breakdown unavailable.</p>'}
      ${this.answer != null ? this.block("Original saved answer JSON", this.answer, true) : ""}</section>${this.block("Raw exported record", data, true)}`;
    this.query("#replay-prev").onclick = () => this.seek(this.index - 1);
    this.query("#replay-next").onclick = () => this.seek(this.index + 1);
    this.query("#replay-play").onclick = () => this.toggle();
    this.query("#replay-progress").oninput = (event) => this.seek(Number(event.target.value));
    this.query(".replay-timeline").onclick = (event) => { const button = event.target.closest("[data-step]"); if (button) this.seek(Number(button.dataset.step)); };
    this.query("#replay-open-source").onclick = () => { this.stop(); this.openTask(this.task.id); };
    this.query("#replay-evidence").onclick = () => this.showEvidence();
    this.query("#replay-recheck").onclick = () => this.recheck();
    this.renderStep();
  }
  query(selector) { return this.root.querySelector(selector); }
  stepTitle(step) {
    const tools = Array.isArray(step?.tool_calls) ? step.tool_calls : [];
    return tools.map((call) => call?.function_name || call?.function?.name || call?.name || "tool").join(", ") || (typeof step?.message === "string" ? step.message.slice(0, 80) : "Recorded message");
  }
  renderTimeline() {
    const start = Math.floor(this.index / 100) * 100, end = Math.min(start + 100, this.steps.length);
    const nav = this.query(".replay-timeline");
    if (start !== this.timelineStart) {
      const e = this.escape;
      nav.innerHTML = this.steps.slice(start, end).map((step, offset) => {
        const index = start + offset;
        return `<button type="button" data-step="${index}" aria-current="false" aria-label="Go to recorded step ${index + 1}"><span>${String(index + 1).padStart(2, "0")}</span><div>${e(step?.source || step?.role || step?.type || "event")}<small>${e(this.stepTitle(step))}</small></div></button>`;
      }).join("");
      this.timelineStart = start; this.timelineActive = null;
      const hint = this.query("#replay-window"); hint.hidden = this.steps.length <= 100;
      hint.textContent = `Timeline steps ${start + 1}–${end} of ${this.steps.length}. Use the step slider, Next, or Play to reach any recorded step.`;
    }
    if (this.timelineActive) this.timelineActive.setAttribute("aria-current", "false");
    this.timelineActive = nav.querySelector(`[data-step="${this.index}"]`);
    if (this.timelineActive) {
      this.timelineActive.setAttribute("aria-current", "true");
      const item = this.timelineActive.getBoundingClientRect(), viewport = nav.getBoundingClientRect();
      if (item.top < viewport.top) nav.scrollTop -= viewport.top - item.top;
      else if (item.bottom > viewport.bottom) nav.scrollTop += item.bottom - viewport.bottom;
      if (item.left < viewport.left) nav.scrollLeft -= viewport.left - item.left;
      else if (item.right > viewport.right) nav.scrollLeft += item.right - viewport.right;
    }
  }
  seek(index) { this.stop(); this.index = Math.max(0, Math.min(this.steps.length - 1, index)); this.renderStep(); }
  toggle() {
    if (this.timer) { this.stop(); this.renderStep(); return; }
    if (!this.steps.length) return;
    if (this.index >= this.steps.length - 1) this.index = 0;
    this.timer = setInterval(() => { this.index++; if (this.index >= this.steps.length - 1) this.stop(); this.renderStep(); }, 1000);
    this.renderStep();
  }
  renderStep() {
    const e = this.escape, step = this.steps[this.index];
    this.query("#replay-position").textContent = `${this.steps.length ? this.index + 1 : 0} / ${this.steps.length}`;
    this.query("#replay-progress").value = this.index;
    this.query("#replay-progress").disabled = !this.steps.length;
    this.query("#replay-prev").disabled = !this.steps.length || this.index === 0;
    this.query("#replay-next").disabled = !this.steps.length || this.index >= this.steps.length - 1;
    const play = this.query("#replay-play"); play.disabled = this.steps.length < 2; play.textContent = this.timer ? "Pause Ⅱ" : "Play ▶"; play.setAttribute("aria-label", this.timer ? "Pause recorded steps" : "Play recorded steps");
    this.renderTimeline();
    if (!this.steps.length) { this.query("#replay-step").innerHTML = '<p class="replay-caption">No recorded steps were exported for this run. Saved scoring evidence may still be available below.</p>'; return; }
    const tools = Array.isArray(step?.tool_calls) ? step.tool_calls : [];
    const observations = Array.isArray(step?.observation?.results) ? step.observation.results : null;
    this.query("#replay-step").innerHTML = `<div class="replay-step-heading"><span>STEP ${e(step?.step_id ?? this.index + 1)} · ${e(step?.source || step?.role || "event")}</span>${step?.timestamp ? `<time>${e(step.timestamp)}</time>` : ""}</div>${this.block("Message", step?.message ?? step?.content ?? (typeof step === "string" ? step : ""))}${tools.map((call) => `<div class="replay-tool"><h4>Tool · ${e(call?.function_name || call?.function?.name || call?.name || "unnamed")}</h4>${this.block("Arguments", call?.arguments ?? call?.function?.arguments)}</div>`).join("")}${observations ? observations.map((result, index) => this.block(`Observation ${index + 1}`, result?.content ?? result)).join("") : this.block("Observation", step?.observation)}${step?.metrics ? this.block("Step metrics", step.metrics, true) : ""}${this.block("Raw step JSON", step, true)}`;
  }
  validBoxes() {
    const page = this.task?.pages?.[0];
    return page && Array.isArray(this.answer?.evidence) ? this.answer.evidence.filter((box) => box?.page === 0 && box.space === page.space && Array.isArray(box.bbox) && box.bbox.length === 4 && box.bbox.every(Number.isFinite) && box.bbox[0] >= 0 && box.bbox[1] >= 0 && box.bbox[2] <= page.width && box.bbox[3] <= page.height && box.bbox[2] > box.bbox[0] && box.bbox[3] > box.bbox[1]) : [];
  }
  answerIssue() {
    const answer = this.answer;
    if (answer == null) return this.data?.submission_error || "No saved answer is available. Legacy event exports may omit the submitted artifact; recheck is unavailable.";
    if (!this.task) return "The source task is unavailable in this catalogue; recheck is unavailable.";
    if (typeof answer !== "object" || Array.isArray(answer) || !["m", "mm", "cm", "ft", "in", "m2", "m²", "mm2", "mm²", "cm2", "cm²", "ft2", "ft²", "in2", "in²", "count"].includes(answer.unit) || !(answer.value === null || (typeof answer.value === "number" && Number.isFinite(answer.value))) || typeof answer.confidence !== "number" || !Number.isFinite(answer.confidence) || answer.confidence < 0 || answer.confidence > 1 || !Array.isArray(answer.evidence) || answer.evidence.length > 32 || this.validBoxes().length !== answer.evidence.length || !Array.isArray(answer.assumptions) || !answer.assumptions.every((item) => typeof item === "string") || (answer.unit === "count" && answer.value !== null && !Number.isInteger(answer.value))) return "The saved answer has invalid fields or evidence geometry. It is preserved unchanged; recheck is unavailable.";
    const page = this.task.pages[0], seen = new Set();
    for (const box of answer.evidence) {
      const key = JSON.stringify([box.page, box.space, box.bbox]);
      if ("point" in box || (box.bbox[2] - box.bbox[0]) * (box.bbox[3] - box.bbox[1]) > .9 * page.width * page.height || seen.has(key) || ("note" in box && typeof box.note !== "string")) return "The saved answer has invalid evidence regions. It is preserved unchanged; recheck is unavailable.";
      seen.add(key);
    }
    return null;
  }
  showEvidence() {
    const node = this.query("#replay-source"), page = this.task.pages[0], boxes = this.validBoxes(), e = this.escape;
    node.hidden = !node.hidden;
    this.query("#replay-evidence").textContent = node.hidden ? "Show saved evidence on source" : "Hide saved evidence on source";
    if (node.hidden) return;
    node.innerHTML = `<p class="replay-caption">Saved model regions · page 0 · ${e(page.width)} × ${e(page.height)} ${e(page.space)}. Coordinates are preserved from the artifact.</p><div class="replay-source-drawing"><img src="/api/tasks/${encodeURIComponent(this.task.id)}/image" alt="${e(this.task.title)} source drawing with saved model evidence"><svg viewBox="0 0 ${page.width} ${page.height}" aria-label="Saved model evidence regions">${boxes.map(({ bbox: [x0, y0, x1, y1] }, index) => `<rect class="evidence-rect" x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}"/><text x="${x0}" y="${y0 - 5}" font-size="22" class="replay-region-number">${index + 1}</text>`).join("")}</svg></div><ol class="replay-regions">${boxes.map((box) => `<li>${e(box.note || "Saved evidence region")}<code>[${box.bbox.map(e).join(", ")}] ${e(box.space)}</code></li>`).join("")}</ol>`;
    node.querySelector("img").onerror = () => { node.querySelector(".replay-source-drawing").textContent = "Source preview unavailable. Open the source task to access the original drawing; saved coordinates remain listed below."; };
  }
  async recheck() {
    if (this.answerIssue()) return;
    const generation = this.generation, button = this.query("#replay-recheck");
    button.disabled = true; this.query("#replay-recheck-result").textContent = "Rechecking saved JSON…";
    try {
      const result = await this.score(this.task.id, this.answer);
      if (generation !== this.generation) return;
      this.query("#replay-recheck-result").innerHTML = `<h4>Recheck reward: ${this.escape(this.text(result.reward))}</h4><p>${result.valid ? "Valid saved answer" : "Invalid saved answer"}. Current verifier result; recorded reward above is unchanged.</p>${this.block("Current verifier details", result, true)}`;
    } catch (error) { if (generation === this.generation) this.query("#replay-recheck-result").textContent = `Recheck failed: ${error.message}`; }
    finally { if (generation === this.generation) button.disabled = false; }
  }
};
