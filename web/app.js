/* Math Practice Player — Client Application (web/app.js) */

let currentDrill = null;
let activeStepByProblem = {}; // { [probId]: number | null }
let saveTimer = null;

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Renders plain text containing inline $...$ LaTeX expressions into safe HTML with KaTeX.
 * Used for prompts, hints, step explanations, diagnostic messages, AND mistake tag pills.
 */
function renderTextWithMath(text) {
  if (!text) return "";
  const parts = String(text).split(/(\$[^$]+\$)/g);
  return parts
    .map((part) => {
      if (part.startsWith("$") && part.endsWith("$") && part.length > 2) {
        const tex = part.slice(1, -1);
        if (window.katex) {
          return window.katex.renderToString(tex, {
            displayMode: false,
            throwOnError: false,
          });
        }
        return `<code>${escapeHtml(tex)}</code>`;
      }
      return escapeHtml(part);
    })
    .join("");
}

/**
 * Renders a pure LaTeX string in block or inline mode via KaTeX.
 */
function renderLatex(tex, displayMode = true) {
  if (!tex) return "";
  if (window.katex) {
    return window.katex.renderToString(String(tex), {
      displayMode,
      throwOnError: false,
    });
  }
  return `<code>${escapeHtml(tex)}</code>`;
}

function showStatus(messageHtml, tone = "warn") {
  const el = document.getElementById("statusBanner");
  if (!el) return;
  el.style.display = "block";
  el.className = `status-banner diag-${tone}`;
  el.innerHTML = messageHtml;
}

function copyPlainText(text, btnEl) {
  navigator.clipboard.writeText(text);
  const prev = btnEl.textContent;
  btnEl.textContent = "Copied!";
  setTimeout(() => {
    btnEl.textContent = prev;
  }, 1100);
}

async function fetchDrillList(preferredDrillId = null) {
  const res = await fetch("/api/drills");
  const data = await res.json();
  const select = document.getElementById("drillFileSelect");
  const drills = data.drills || [];

  if (drills.length === 0) {
    select.innerHTML = `<option value="">No drill .json found — click + Generate</option>`;
    return;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const targetId = preferredDrillId || urlParams.get("drill") || drills[0].drillId;

  select.innerHTML = drills
    .map((d) => {
      const sel = d.drillId === targetId ? "selected" : "";
      return `<option value="${escapeHtml(d.drillId)}" ${sel}>${escapeHtml(d.drillId)} · ${escapeHtml(d.unitCode)} (${d.questionCount} Qs · ${escapeHtml(d.difficultyMode)})</option>`;
    })
    .join("");

  await loadDrillById(select.value || drills[0].drillId);
}

async function handleSelectDrillFile(drillId) {
  if (!drillId) return;
  const url = new URL(window.location.href);
  url.searchParams.set("drill", drillId);
  window.history.replaceState({}, "", url.toString());
  await loadDrillById(drillId);
}

async function loadDrillById(drillId) {
  const res = await fetch(`/api/drill?id=${encodeURIComponent(drillId)}`);
  if (!res.ok) {
    showStatus(`Could not load drill <code>${escapeHtml(drillId)}</code>.`, "fail");
    return;
  }
  currentDrill = await res.json();
  activeStepByProblem = {};
  (currentDrill.problems || []).forEach((p) => {
    activeStepByProblem[p.id] = null;
    if (!p.state) {
      p.state = { userInput: "", score: null, divergedStep: null, mistakes: [], lastCheck: null };
    }
  });

  // Sync top config selectors with the loaded drill's config
  if (currentDrill.config) {
    const cSel = document.getElementById("cfgCount");
    const dSel = document.getElementById("cfgDifficulty");
    if (cSel && currentDrill.config.questionCount) cSel.value = String(currentDrill.config.questionCount);
    if (dSel && currentDrill.config.difficulty) dSel.value = String(currentDrill.config.difficulty);
  }

  renderHeaderCard();
  renderAllProblems();
  updateScoreBadge();
}

async function handleGenerateNewDrill() {
  const unitCode = document.getElementById("cfgUnit").value;
  const count = parseInt(document.getElementById("cfgCount").value, 10);
  const difficulty = document.getElementById("cfgDifficulty").value;
  const btn = document.getElementById("btnGenerate");

  btn.disabled = true;
  showStatus(
    `Generating and verifying <strong>${count} questions</strong> (${escapeHtml(difficulty)}) with SymPy...`,
    "warn"
  );

  try {
    const res = await fetch("/api/generate-drill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unitCode, count, difficulty }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Failed to generate drill");
    }
    showStatus(
      `Generated &amp; verified <strong>${escapeHtml(data.drillId)}</strong> (<code>${escapeHtml(data.localFilePath)}</code>) with ${count} questions.`,
      "pass"
    );
    const url = new URL(window.location.href);
    url.searchParams.set("drill", data.drillId);
    window.history.replaceState({}, "", url.toString());
    await fetchDrillList(data.drillId);
  } catch (err) {
    showStatus(`Generation error: ${escapeHtml(err.message)}`, "fail");
  } finally {
    btn.disabled = false;
  }
}

function renderHeaderCard() {
  const el = document.getElementById("drillHeaderCard");
  if (!currentDrill || !el) return;
  const d = currentDrill;
  const unitBadge = d.unitNotionUrl
    ? `<a class="notion-ref-badge" href="${escapeHtml(d.unitNotionUrl)}" target="_blank" rel="noopener">↗ Notion Unit: ${escapeHtml(d.unitCode)} · ${escapeHtml(d.unitTitle)}</a>`
    : `<span class="badge">Unit: ${escapeHtml(d.unitCode)}</span>`;

  el.innerHTML = `
    <div class="badge-row">
      <span class="badge">${escapeHtml(d.drillId)}</span>
      ${unitBadge}
      <span class="badge">${d.problems.length} Questions (${escapeHtml(d.config?.difficultyMode || "Mixed")})</span>
      <span class="badge">File: ${escapeHtml(d.localFilePath)}</span>
    </div>
    <h1>${escapeHtml(d.unitTitle)} (${escapeHtml(d.unitCode)}) — Interactive Math Workspace</h1>
    <p class="subtitle">
      Solve on physical scratch paper, verify intermediate checkpoints, click any step row to highlight the equation &amp; explanation together, mark the exact line where your paper diverged, and sync results to Notion.
    </p>
  `;
}

function getProblem(probId) {
  return (currentDrill?.problems || []).find((p) => p.id === probId);
}

function renderAllProblems() {
  const root = document.getElementById("problemsRoot");
  if (!currentDrill || !root) return;

  root.innerHTML = currentDrill.problems
    .map((p, idx) => {
      const refBadgesHtml = (p.referenceBadges || [])
        .map((b) =>
          b.notionUrl
            ? `<a class="notion-ref-badge" href="${escapeHtml(b.notionUrl)}" target="_blank" rel="noopener">↗ ${escapeHtml(b.code)} · ${escapeHtml(b.title)}</a>`
            : `<span class="badge">${escapeHtml(b.code)}</span>`
        )
        .join("");

      const contextHtml = p.context
        ? `<span class="context-pill">${renderTextWithMath(p.context)}</span>`
        : "";

      const displayBoxHtml = p.display
        ? `<div class="prompt-math-box">${renderLatex(p.display, true)}</div>`
        : "";

      // Input widget adapts to answerSpec.type
      let inputWidgetHtml = "";
      if (p.answerSpec?.type === "choice") {
        const opts = p.answerSpec.options || [];
        inputWidgetHtml = `
          <div class="choice-group" id="choices-${p.id}">
            ${opts
              .map((o) => {
                const sel = String(p.state?.userInput) === String(o.id) ? "selected" : "";
                return `<button type="button" class="choice-btn ${sel}" onclick="selectChoiceOption('${p.id}', '${escapeHtml(o.id)}')">${renderTextWithMath(o.label)}</button>`;
              })
              .join("")}
          </div>
        `;
      } else {
        inputWidgetHtml = `
          <input
            type="text"
            id="ans-${p.id}"
            class="answer-input"
            value="${escapeHtml(p.state?.userInput || "")}"
            placeholder="${escapeHtml(p.inputHint || "Type final answer or solve on paper...")}"
            oninput="handleInputEdit('${p.id}', this.value)"
            onkeydown="if(event.key==='Enter') checkProblemAnswer('${p.id}')"
          />
        `;
      }

      const stepsHtml = (p.steps || [])
        .map((st, sIdx) => {
          const isDiverged = p.state?.divergedStep === sIdx;
          return `
            <div class="step-row ${isDiverged ? "diverged-step" : ""}" onclick="toggleStepHighlight('${p.id}', ${sIdx}, event)">
              <div class="step-math">${renderLatex(st.latex, true)}</div>
              <div class="step-explain"><strong>Step ${sIdx + 1}:</strong> ${renderTextWithMath(st.explain)}</div>
              <button
                type="button"
                class="diverge-btn ${isDiverged ? "active" : ""}"
                onclick="markDivergedStep('${p.id}', ${sIdx}, event)"
              >${isDiverged ? `✗ Diverged at Step ${sIdx + 1}` : "✗ My Paper Diverged Here"}</button>
            </div>
          `;
        })
        .join("");

      const sc = p.state?.score;
      const c1 = sc === 1 ? "selected-correct" : "";
      const cHalf = sc === 0.5 ? "selected-partial" : "";
      const c0 = sc === 0 ? "selected-wrong" : "";

      return `
        <article class="problem-card" id="card-${p.id}">
          <div class="problem-header">
            <div class="problem-title-group">
              <span class="problem-num">Problem ${idx + 1} <span style="color:var(--muted); font-weight:400;">(${escapeHtml(p.id)})</span></span>
              ${contextHtml}
              ${refBadgesHtml}
            </div>
            <span class="level-pill">Level ${p.level}</span>
          </div>

          <div class="prompt-text">${renderTextWithMath(p.prompt)}</div>
          ${displayBoxHtml}

          <div class="cas-box">
            <span><strong>Plain-Text / CAS Input:</strong> <code>${escapeHtml(p.plainText || "")}</code></span>
            <button type="button" onclick="copyPlainText(${JSON.stringify(p.plainText || "")}, this)">Copy Plain Text</button>
          </div>

          <div class="workspace-row">
            ${inputWidgetHtml}
            <button type="button" class="btn-primary" onclick="checkProblemAnswer('${p.id}')">Check Answer</button>
            <button type="button" onclick="toggleBox('hint-${p.id}')">Checkpoint Hint</button>
            <button type="button" onclick="toggleBox('sol-${p.id}')">Reveal Step-by-Step Solution</button>
          </div>

          <div id="diag-${p.id}" class="diag-feedback"></div>
          <div id="hint-${p.id}" class="hint-box"><strong>Intermediate Paper Checkpoint:</strong> ${renderTextWithMath(p.checkpointHint)}</div>

          <div id="sol-${p.id}" class="solution-panel">
            <div class="solution-header">
              <span class="verified-ans-chip">
                <strong>Verified Answer:</strong>
                <span>${renderLatex(p.answerDisplay, false)}</span>
                <span style="color:var(--muted);">(${escapeHtml(p.category)} · ${escapeHtml(p.levelLabel)})</span>
              </span>
              <span>Click any step row to focus &amp; highlight equation + explanation</span>
            </div>

            <div class="steps-container" id="steps-${p.id}">
              ${stepsHtml}
            </div>

            <div class="grading-bar">
              <div class="grade-btns">
                <span style="font-size:12.5px; color:var(--muted);">Paper Self-Grade:</span>
                <button type="button" id="g1-${p.id}" class="grade-btn ${c1}" onclick="setProblemScore('${p.id}', 1)">✓ Correct (1.0)</button>
                <button type="button" id="ghalf-${p.id}" class="grade-btn ${cHalf}" onclick="setProblemScore('${p.id}', 0.5)">~ Partial (0.5)</button>
                <button type="button" id="g0-${p.id}" class="grade-btn ${c0}" onclick="setProblemScore('${p.id}', 0)">✗ Miss (0.0)</button>
              </div>
              <span style="font-size:12px; color:var(--muted);">Tag root-cause mistake (if any):</span>
            </div>

            <div class="mistake-pills" id="pills-${p.id}"></div>
          </div>
        </article>
      `;
    })
    .join("");

  currentDrill.problems.forEach((p) => {
    renderMistakePills(p.id);
    if (p.state?.lastCheck) {
      renderDiagnosticBox(p.id, p.state.lastCheck);
    }
  });
}

function toggleBox(elId) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.style.display = el.style.display === "block" ? "none" : "block";
}

function handleInputEdit(probId, val) {
  const p = getProblem(probId);
  if (!p) return;
  p.state.userInput = val;
  scheduleSaveState();
}

function selectChoiceOption(probId, optId) {
  const p = getProblem(probId);
  if (!p) return;
  p.state.userInput = optId;
  const container = document.getElementById(`choices-${probId}`);
  if (container) {
    const opts = p.answerSpec?.options || [];
    container.querySelectorAll(".choice-btn").forEach((btn, idx) => {
      if (opts[idx] && String(opts[idx].id) === String(optId)) {
        btn.classList.add("selected");
      } else {
        btn.classList.remove("selected");
      }
    });
  }
  checkProblemAnswer(probId);
}

function renderDiagnosticBox(probId, result) {
  const diagEl = document.getElementById(`diag-${probId}`);
  if (!diagEl || !result) return;

  const toneMap = {
    correct: "diag-pass",
    equivalent_not_in_form: "diag-warn",
    partial: "diag-warn",
    parse_error: "diag-warn",
    incorrect: "diag-fail",
  };
  diagEl.className = `diag-feedback ${toneMap[result.verdict] || "diag-warn"}`;

  const compsHtml = (result.components || [])
    .map((c) => {
      const cls = c.ok ? "comp-ok" : "comp-bad";
      const sym = c.ok ? "✓" : "✗";
      return `<span class="comp-chip ${cls}">${sym} ${renderTextWithMath(c.label)}</span>`;
    })
    .join("");

  const extraMsgs = (result.diagnostics || [])
    .map((d) => `<div style="margin-top:4px;">• ${renderTextWithMath(d.message)}</div>`)
    .join("");

  diagEl.innerHTML = `
    <div><strong>${renderTextWithMath(result.message)}</strong></div>
    ${extraMsgs}
    ${compsHtml ? `<div class="comp-chips">${compsHtml}</div>` : ""}
  `;
}

async function checkProblemAnswer(probId) {
  const p = getProblem(probId);
  if (!p) return;
  const inputVal = (p.state?.userInput || "").trim();

  if (!inputVal) {
    renderDiagnosticBox(probId, {
      verdict: "parse_error",
      message: "Solved on paper? Open 'Reveal Step-by-Step Solution' below to compare your derivation and click your paper grade.",
      components: [],
      diagnostics: [],
    });
    return;
  }

  try {
    const res = await fetch("/api/check-answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answerSpec: p.answerSpec, input: inputVal }),
    });
    const result = await res.json();
    p.state.lastCheck = result;
    renderDiagnosticBox(probId, result);

    // Map verdict to automatic score + mistake tags
    if (result.verdict === "correct") {
      setProblemScore(probId, 1);
    } else if (result.verdict === "equivalent_not_in_form" || result.verdict === "partial") {
      setProblemScore(probId, 0.5);
    } else if (result.verdict === "incorrect") {
      setProblemScore(probId, 0);
    }

    // Auto-activate matching mistake tags from diagnostic codes
    const codes = new Set((result.diagnostics || []).map((d) => d.code));
    (currentDrill.mistakeTags || []).forEach((tag) => {
      if ((tag.autoFrom || []).some((c) => codes.has(c))) {
        addMistakeTag(probId, tag.id);
      }
    });
    if (result.verdict === "incorrect" && p.commonTrapTag && (p.state.mistakes || []).length === 0) {
      addMistakeTag(probId, p.commonTrapTag);
    }
    scheduleSaveState();
  } catch (err) {
    renderDiagnosticBox(probId, {
      verdict: "parse_error",
      message: `Error contacting SymPy checker: ${err.message}`,
      components: [],
      diagnostics: [],
    });
  }
}

function toggleStepHighlight(probId, stepIdx, event) {
  if (event?.target?.classList?.contains("diverge-btn")) return;
  activeStepByProblem[probId] = activeStepByProblem[probId] === stepIdx ? null : stepIdx;

  const container = document.getElementById(`steps-${probId}`);
  if (!container) return;
  const rows = container.querySelectorAll(".step-row");
  const active = activeStepByProblem[probId];

  if (active === null) {
    container.classList.remove("has-active");
    rows.forEach((r) => r.classList.remove("active-step"));
  } else {
    container.classList.add("has-active");
    rows.forEach((r, idx) => {
      if (idx === active) r.classList.add("active-step");
      else r.classList.remove("active-step");
    });
  }
}

function markDivergedStep(probId, stepIdx, event) {
  event.stopPropagation();
  const p = getProblem(probId);
  if (!p) return;

  if (p.state.divergedStep === stepIdx) {
    p.state.divergedStep = null;
  } else {
    p.state.divergedStep = stepIdx;
    if (p.commonTrapTag) addMistakeTag(probId, p.commonTrapTag);
    if (p.state.score === null || p.state.score === 1) {
      setProblemScore(probId, 0.5);
    }
  }

  const container = document.getElementById(`steps-${probId}`);
  if (container) {
    container.querySelectorAll(".step-row").forEach((r, idx) => {
      const btn = r.querySelector(".diverge-btn");
      if (idx === p.state.divergedStep) {
        r.classList.add("diverged-step");
        if (btn) {
          btn.classList.add("active");
          btn.textContent = `✗ Diverged at Step ${idx + 1}`;
        }
      } else {
        r.classList.remove("diverged-step");
        if (btn) {
          btn.classList.remove("active");
          btn.textContent = "✗ My Paper Diverged Here";
        }
      }
    });
  }
  scheduleSaveState();
}

function setProblemScore(probId, val) {
  const p = getProblem(probId);
  if (!p) return;
  p.state.score = val;
  const b1 = document.getElementById(`g1-${probId}`);
  const bHalf = document.getElementById(`ghalf-${probId}`);
  const b0 = document.getElementById(`g0-${probId}`);
  if (b1 && bHalf && b0) {
    b1.className = "grade-btn" + (val === 1 ? " selected-correct" : "");
    bHalf.className = "grade-btn" + (val === 0.5 ? " selected-partial" : "");
    b0.className = "grade-btn" + (val === 0 ? " selected-wrong" : "");
  }
  updateScoreBadge();
  scheduleSaveState();
}

function addMistakeTag(probId, tagId) {
  const p = getProblem(probId);
  if (!p) return;
  if (!Array.isArray(p.state.mistakes)) p.state.mistakes = [];
  if (!p.state.mistakes.includes(tagId)) {
    p.state.mistakes.push(tagId);
    renderMistakePills(probId);
  }
}

function toggleMistakeTag(probId, tagId) {
  const p = getProblem(probId);
  if (!p) return;
  if (!Array.isArray(p.state.mistakes)) p.state.mistakes = [];
  const idx = p.state.mistakes.indexOf(tagId);
  if (idx >= 0) p.state.mistakes.splice(idx, 1);
  else p.state.mistakes.push(tagId);
  renderMistakePills(probId);
  scheduleSaveState();
}

function renderMistakePills(probId) {
  const root = document.getElementById(`pills-${probId}`);
  const p = getProblem(probId);
  if (!root || !p || !currentDrill) return;
  const selected = new Set(p.state?.mistakes || []);

  root.innerHTML = (currentDrill.mistakeTags || [])
    .map((tag) => {
      const active = selected.has(tag.id) ? "active" : "";
      return `<span class="mistake-pill ${active}" onclick="toggleMistakeTag('${probId}', '${escapeHtml(tag.id)}')">${renderTextWithMath(tag.label)}</span>`;
    })
    .join("");
}

function computeSummary() {
  if (!currentDrill) return null;
  let earned = 0;
  const maxScore = currentDrill.problems.length;
  const tagMap = {};
  (currentDrill.mistakeTags || []).forEach((t) => {
    tagMap[t.id] = t;
  });

  const mistakeNames = new Set();
  const divergedList = [];

  currentDrill.problems.forEach((p) => {
    const sc = p.state?.score;
    if (typeof sc === "number") earned += sc;
    (p.state?.mistakes || []).forEach((tid) => {
      const t = tagMap[tid];
      mistakeNames.add(t ? t.name : tid);
    });
    if (typeof p.state?.divergedStep === "number") {
      const sIdx = p.state.divergedStep;
      const st = p.steps[sIdx];
      divergedList.push(`${p.id} (Step ${sIdx + 1}: ${st ? st.explain : "Diverged"})`);
    } else if (typeof sc === "number" && sc < 1 && (p.state?.mistakes || []).length > 0) {
      const labels = p.state.mistakes.map((tid) => tagMap[tid]?.name || tid).join(", ");
      divergedList.push(`${p.id} (${labels})`);
    }
  });

  const pct = maxScore > 0 ? Math.round((earned / maxScore) * 1000) / 10 : 0;
  return {
    practiceStatus: maxScore > 0 && earned / maxScore >= 0.8 ? "Graded" : "Needs Retry",
    score: earned,
    maxScore,
    accuracyPct: pct,
    mistakeCategories: Array.from(mistakeNames),
    divergedStepsSummary: divergedList.length > 0 ? divergedList.join(" | ") : "No diverged steps logged.",
    attemptDate: new Date().toISOString().slice(0, 10),
  };
}

function updateScoreBadge() {
  const s = computeSummary();
  const el = document.getElementById("liveScoreBadge");
  if (!s || !el) return;
  el.textContent = `Score: ${s.score} / ${s.maxScore} (${s.accuracyPct}%)`;
}

function scheduleSaveState() {
  if (!currentDrill) return;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    currentDrill.sessionSummary = {
      ...(currentDrill.sessionSummary || {}),
      ...computeSummary(),
    };
    try {
      await fetch("/api/save-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentDrill),
      });
    } catch (_) {
      // ignore transient network errors on background save
    }
  }, 300);
}

async function handleSyncToNotion() {
  if (!currentDrill) return;
  const btn = document.getElementById("btnSyncNotion");
  btn.disabled = true;

  currentDrill.sessionSummary = {
    ...(currentDrill.sessionSummary || {}),
    ...computeSummary(),
  };

  showStatus(
    `Syncing <strong>${escapeHtml(currentDrill.drillId)}</strong> (${currentDrill.sessionSummary.score}/${currentDrill.sessionSummary.maxScore}) and problem toggles to Notion...`,
    "warn"
  );

  try {
    const res = await fetch("/api/sync-notion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentDrill),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Sync failed");
    }
    showStatus(
      `Synced to Notion! Updated <strong>${escapeHtml(currentDrill.drillId)}</strong> (${currentDrill.sessionSummary.score}/${currentDrill.sessionSummary.maxScore} · ${currentDrill.sessionSummary.accuracyPct}%) in <em>Learning Practice &amp; Drills</em> and appended attempt log to <strong>${escapeHtml(currentDrill.unitCode)}</strong>.`,
      "pass"
    );
  } catch (err) {
    showStatus(`Notion Sync error: ${escapeHtml(err.message)}`, "fail");
  } finally {
    btn.disabled = false;
  }
}

function initTheme() {
  try {
    const saved = localStorage.getItem("studio_theme");
    if (saved === "light") {
      document.documentElement.classList.add("light");
      document.body.classList.add("light");
      updateThemeBtnText("light");
    } else {
      updateThemeBtnText("dark");
    }
  } catch (e) {
    // ignore
  }
}

function toggleTheme() {
  const isLight = document.documentElement.classList.toggle("light");
  document.body.classList.toggle("light", isLight);
  const theme = isLight ? "light" : "dark";
  try {
    localStorage.setItem("studio_theme", theme);
  } catch (e) {
    // ignore
  }
  updateThemeBtnText(theme);
}

function updateThemeBtnText(theme) {
  const btn = document.getElementById("btnThemeToggle");
  if (btn) {
    btn.innerHTML = theme === "light" ? "🌙 Dark" : "☀️ Light";
    btn.title = theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  initTheme();
  fetchDrillList();
});
