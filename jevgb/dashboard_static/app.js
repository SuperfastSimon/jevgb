/* JevGB dashboard. No dependencies, no network calls except to the local `jevgb dashboard` server. */
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const fmt = (n) => (n === null || n === undefined) ? "–" : Number(n).toLocaleString("en-US");
  const signed = (n) => (n === null || n === undefined) ? "–" : (n > 0 ? "+" : n < 0 ? "−" : "") + fmt(Math.abs(n));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const LIVE = location.protocol.startsWith("http");
  // Project link for the footer. A plain <a> with ?ref=dashboard; the dashboard never sends data anywhere.
  const PROJECT_URL = "https://github.com/SuperfastSimon/jevgb";
  const ACTION_LABEL = {
    handoff_build: "Compact brief instead of full chat", build_result_relay: "Short result instead of full session",
    reuse_cache: "Fresh artifact reused", stop_retry: "Repeated failure stopped", skip_duplicate_call: "Identical tool call skipped",
    research_capped: "Research capped", chat_only: "Answered without tools", run_deterministic: "Bounded lookup",
    ask_human: "Paused for approval", allow_subagent: "Subagent allowed", proceed_full: "Normal work",
  };
  let state = { records: [], briefs: {}, simulated: false, source: "", errors: [] };
  let current = null;

  function quality(basis) {
    const b = (basis || "").toLowerCase();
    if (b.startsWith("not_measurable")) return "none";
    if (b.startsWith("caller")) return "caller";
    if (b.includes("estimate")) return "estimate";
    return "measured";
  }
  const QUALITY_LABEL = { measured: "measured", estimate: "estimate", caller: "caller-reported", none: "not measurable" };

  function parseJsonl(text) {
    const records = [], errors = [];
    text.split(/\r?\n/).forEach((line, i) => {
      if (!line.trim()) return;
      try { const r = JSON.parse(line); if (r && typeof r === "object") records.push(r); else throw 0; }
      catch { errors.push(`line ${i + 1}: not valid JSON, skipped`); }
    });
    return { records, errors };
  }

  function summarize(recs) {
    const measured = recs.filter((r) => r.baseline_tokens !== null && r.baseline_tokens !== undefined);
    const sum = (a, k) => a.reduce((t, r) => t + (Number(r[k]) || 0), 0);
    const base = sum(measured, "baseline_tokens"), act = sum(measured, "actual_tokens"), over = sum(recs, "overhead_tokens");
    const byAction = {};
    recs.forEach((r) => {
      const a = byAction[r.action] ||= { tasks: 0, base: 0, act: 0, over: 0, net: 0, unmeasured: 0 };
      a.tasks++; a.over += Number(r.overhead_tokens) || 0;
      if (r.baseline_tokens === null || r.baseline_tokens === undefined) { a.unmeasured++; a.act += Number(r.actual_tokens) || 0; a.net -= Number(r.overhead_tokens) || 0; }
      else { a.base += Number(r.baseline_tokens); a.act += Number(r.actual_tokens) || 0; a.net += Number(r.net_saved_tokens) || 0; }
    });
    return {
      tasks: recs.length, measured: measured.length, base, act, over, net: base - act - over,
      negative: measured.filter((r) => Number(r.net_saved_tokens) < 0).length, byAction,
      estimators: [...new Set(recs.map((r) => r.estimator).filter(Boolean))],
    };
  }

  function setSource(label, kind) {
    $("#source").innerHTML = `Source: <b>${esc(label)}</b>`;
    $("#reload").hidden = kind !== "live";
  }

  function showError(msgs) {
    const el = $("#error");
    if (!msgs || !msgs.length) { el.hidden = true; el.textContent = ""; return; }
    el.hidden = false;
    el.innerHTML = `<strong>Some data could not be read.</strong> ${msgs.slice(0, 4).map(esc).join(" · ")}${msgs.length > 4 ? ` · and ${msgs.length - 4} more` : ""}`;
  }

  function render() {
    const recs = state.records;
    const empty = !recs.length;
    $("#empty").hidden = !empty;
    $("#content").hidden = empty;
    const simCount = recs.filter((r) => r.simulated).length;
    $("#sim-banner").hidden = !(state.simulated || simCount);
    if (simCount && simCount < recs.length) $("#sim-text").textContent = `${simCount} of ${recs.length} records are simulated examples, not real usage.`;
    showError(state.errors);
    if (empty) return;

    const s = summarize(recs);
    const net = $("#k-net");
    net.textContent = signed(s.net);
    net.className = "kpi-value " + (s.net >= 0 ? "pos" : "neg");
    $("#k-pct").textContent = pctText(s.net, s.base);
    $("#k-base").textContent = fmt(s.base);
    $("#k-act").textContent = fmt(s.act);
    $("#k-over").textContent = fmt(s.over);
    $("#k-tasks").textContent = `${fmt(s.tasks)}`;
    $("#k-neg").textContent = `${s.measured} measurable · ${s.negative} cost more than saved`;
    $("#estimator").innerHTML = `All numbers are <strong>estimates</strong> by <code>${esc(s.estimators.join(", ") || "unknown estimator")}</code>. Overhead of tasks without a baseline still counts against the total.`;

    // By action
    const acts = Object.entries(s.byAction).sort((a, b) => (b[1].base + b[1].over) - (a[1].base + a[1].over));
    const max = Math.max(1, ...acts.map(([, a]) => Math.max(a.base, a.act + a.over)));
    $("#actions").innerHTML = acts.map(([k, a]) => `
      <li class="bar-row">
        <div class="bar-name">${esc(k)}<small>${esc(ACTION_LABEL[k] || "")} · ${a.tasks} task${a.tasks === 1 ? "" : "s"}</small></div>
        <div class="track" role="img" aria-label="${esc(k)}: baseline ${fmt(a.base)}, actual plus overhead ${fmt(a.act + a.over)} tokens">
          <span class="b base" style="width:${(100 * a.base / max).toFixed(2)}%"></span>
          <span class="b act" style="width:${Math.max(0.6, 100 * (a.act + a.over) / max).toFixed(2)}%"></span>
        </div>
        <div class="bar-val"><b class="${a.net >= 0 ? "pos" : "neg"}">${signed(a.net)}</b><span>${fmt(a.base)} → ${fmt(a.act + a.over)}</span></div>
      </li>`).join("");

    // Handoffs
    const ho = recs.filter((r) => r.action === "handoff_build");
    const relays = Object.fromEntries(recs.filter((r) => r.action === "build_result_relay").map((r) => [r.task_id, r]));
    $("#handoffs").innerHTML = ho.length ? ho.map((r) => {
      const ratio = r.baseline_tokens ? Math.min(100, 100 * r.actual_tokens / r.baseline_tokens) : 100;
      const relay = relays[r.task_id];
      return `<article class="card">
        <h3>${esc(r.goal || r.task_id)}</h3>
        <div class="meta"><span>Full chat <b>${fmt(r.baseline_tokens)}</b></span><span>Brief <b>${fmt(r.actual_tokens)}</b></span><span>Net <b class="${(r.net_saved_tokens ?? 0) >= 0 ? "pos" : "neg"}">${signed(r.net_saved_tokens)}</b></span></div>
        <div class="ratio" role="img" aria-label="Brief is ${ratio.toFixed(0)}% of the full chat"><i style="width:${ratio.toFixed(1)}%"></i></div>
        ${relay ? `<p class="relay"><b>Result relayed</b> · ${esc((relay.extra?.relay || "").split("\n")[0].replace(/^Grok Build:\s*/, ""))}</p>` : ""}
        <div class="row"><span class="muted" style="font: 12px var(--mono)">${esc(r.task_id)}${relay ? ` · relay ${fmt(relay.baseline_tokens)} → ${fmt(relay.actual_tokens)}` : ""}</span>
        <button class="btn btn-quiet" type="button" data-brief="${esc(r.task_id)}">View brief</button></div>
      </article>`;
    }).join("") : `<p class="muted">No handoffs yet. Code and repo tasks are routed to Grok Build with a compact brief.</p>`;

    // Guards
    const mini = (sel, list, fn, none) => { $(sel).innerHTML = list.length ? list.map(fn).join("") : `<li class="none">${none}</li>`; };
    mini("#g-cache", recs.filter((r) => r.action === "reuse_cache"), (r) => `<li>${esc(r.goal)}<span>${signed(r.net_saved_tokens)} tokens · ${esc(QUALITY_LABEL[quality(r.baseline_basis)])}</span></li>`, "No cache hits yet");
    mini("#g-retry", recs.filter((r) => r.action === "stop_retry"), (r) => `<li>${esc(r.goal)}<span>${r.extra?.retry ? r.extra.retry.same_approach_failures + "× same approach · " : ""}${signed(r.net_saved_tokens)} tokens</span></li>`, "No retries stopped");
    mini("#g-dupe", recs.filter((r) => r.action === "skip_duplicate_call"), (r) => `<li>${esc(r.goal)}<span>${signed(r.net_saved_tokens)} tokens</span></li>`, "No duplicate calls");

    // Filters + table
    const sel = $("#act-filter"), keep = sel.value;
    sel.innerHTML = `<option value="">All actions</option>` + Object.keys(s.byAction).sort().map((k) => `<option ${k === keep ? "selected" : ""}>${esc(k)}</option>`).join("");
    renderRows();
  }

  function renderRows() {
    const q = $("#q").value.trim().toLowerCase(), act = $("#act-filter").value;
    const rows = state.records.filter((r) => (!act || r.action === act) &&
      (!q || [r.goal, r.action, r.task_id].join(" ").toLowerCase().includes(q)));
    $("#no-match").hidden = rows.length > 0;
    $("#rows").innerHTML = rows.map((r, i) => {
      const qy = quality(r.baseline_basis);
      const t = r.ts ? new Date(r.ts) : null;
      const time = t && !isNaN(t) ? t.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "–";
      return `<tr tabindex="0" data-i="${state.records.indexOf(r)}" aria-label="Open details for ${esc(r.task_id)}">
        <td class="q" style="color:var(--muted)">${esc(time)}</td>
        <td class="goal">${esc(r.goal || "(no goal)")}<small>${esc(r.task_id)}${r.simulated ? " · simulated" : ""}</small></td>
        <td><span class="tag ${esc(r.action)}">${esc(r.action)}</span></td>
        <td class="num">${fmt(r.baseline_tokens)}</td><td class="num">${fmt(r.actual_tokens)}</td><td class="num">${fmt(r.overhead_tokens)}</td>
        <td class="num ${r.net_saved_tokens === null || r.net_saved_tokens === undefined ? "" : r.net_saved_tokens >= 0 ? "pos" : "neg"}"><b>${signed(r.net_saved_tokens)}</b></td>
        <td><span class="q ${qy}" title="${esc(r.baseline_basis)}">${esc(QUALITY_LABEL[qy])}</span></td></tr>`;
    }).join("");
  }

  // Minimal, safe markdown for briefs: headings, bullets, fenced code, paragraphs.
  function md(text) {
    const out = []; let list = false, code = null;
    const close = () => { if (list) { out.push("</ul>"); list = false; } };
    for (const line of text.split("\n")) {
      if (code !== null) { if (line.startsWith("```")) { out.push(`<pre>${esc(code.join("\n"))}</pre>`); code = null; } else code.push(line); continue; }
      if (line.startsWith("```")) { close(); code = []; continue; }
      const inline = (s) => esc(s).replace(/`([^`]+)`/g, "<code>$1</code>");
      let m;
      if ((m = line.match(/^(#{1,3})\s+(.*)/))) { close(); out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); }
      else if ((m = line.match(/^\s*[-*]\s+(.*)/))) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${inline(m[1])}</li>`); }
      else if (line.trim()) { close(); out.push(`<p>${inline(line)}</p>`); }
      else close();
    }
    if (code !== null) out.push(`<pre>${esc(code.join("\n"))}</pre>`);
    close();
    return out.join("");
  }

  async function getBrief(taskId) {
    if (state.briefs[taskId]) return state.briefs[taskId];
    if (LIVE) {
      const r = await fetch(`/api/brief?task_id=${encodeURIComponent(taskId)}`);
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `HTTP ${r.status}`);
      return (state.briefs[taskId] = (await r.json()).markdown);
    }
    throw new Error("Brief not available in this file. Use “Open a brief file…” or run `jevgb dashboard`.");
  }

  async function openViewer({ rec = null, markdown = null, name = "" }) {
    current = { rec, markdown: "" };
    $("#viewer-title").textContent = rec ? (rec.goal || rec.task_id) : name || "Brief";
    $("#viewer-eyebrow").textContent = rec ? `${rec.action} · ${rec.task_id}${rec.simulated ? " · simulated" : ""}` : "Brief file";
    const meta = rec ? [
      ["Baseline", fmt(rec.baseline_tokens)], ["Actual", fmt(rec.actual_tokens)], ["Overhead", fmt(rec.overhead_tokens)],
      ["Net", signed(rec.net_saved_tokens)], ["Basis", rec.baseline_basis || "–"],
    ] : [];
    $("#viewer-meta").innerHTML = meta.map(([k, v]) => `<span>${k} <b>${esc(v)}</b></span>`).join("");
    const isBrief = !rec || rec.action === "handoff_build";
    $("#copy-cmd").hidden = !isBrief; $("#toggle-raw").hidden = !isBrief;
    $("#viewer-raw").hidden = true; $("#toggle-raw").setAttribute("aria-pressed", "false"); $("#toggle-raw").textContent = "Show raw markdown";
    $("#copy-status").textContent = "";
    const body = $("#viewer-body");
    if (!$("#viewer").open) $("#viewer").showModal();
    if (!isBrief) {
      const extra = rec.extra ? `<h2>Details</h2><pre>${esc(JSON.stringify(rec.extra, null, 2))}</pre>` : "";
      body.innerHTML = `<h2>Why</h2><p>${esc(ACTION_LABEL[rec.action] || rec.action)}.</p>${extra}`;
      return;
    }
    body.innerHTML = `<p class="muted">Loading brief…</p>`;
    try {
      const text = markdown ?? await getBrief(rec.task_id);
      current.markdown = text;
      body.innerHTML = md(text);
      $("#viewer-raw").textContent = text;
    } catch (e) {
      body.innerHTML = `<div class="alert" role="alert"><strong>Could not load this brief.</strong> ${esc(e.message)}</div>`;
    }
  }

  // A percentage of a tiny baseline is noise (e.g. "-4990%"), so only show it with enough data and cap the range.
  const MIN_PCT_BASE = 1000;
  function pctText(net, base) {
    if (!base) return "No measurable baseline yet";
    if (base < MIN_PCT_BASE) return `Too little measurable baseline for a percentage (${fmt(base)} tokens)`;
    const pct = 100 * net / base;
    if (pct < -100) return "Cost more than the measurable baseline (estimated)";
    return `${pct.toFixed(1)}% of measurable baseline (estimated)`;
  }

  async function loadLive() {
    try {
      const r = await fetch("/api/tokens", { cache: "no-store" });
      // No local server behind this page (static host such as GitHub Pages): show the simulated demo.
      if (r.status === 404 && window.JGB_DEMO) return loadDemo(false);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      state = { records: d.records || [], briefs: {}, simulated: false, source: d.source, errors: d.errors || [] };
      setSource(d.source || "live log", "live");
    } catch (e) {
      state = { records: [], briefs: {}, simulated: false, errors: [`Could not reach the local server: ${e.message}`] };
      setSource("unavailable", "live");
    }
    render();
  }

  function loadDemo(focus = true) {
    const d = window.JGB_DEMO;
    if (!d) { state.errors = ["Simulated demo data not found. Run scripts/demo_savings.py to generate it."]; render(); return; }
    state = { records: d.records, briefs: d.briefs || {}, simulated: true, errors: [] };
    setSource("simulated demo", "demo");
    render();
    if (focus === true) $("#main").focus();
  }

  // Events
  $("#demo").addEventListener("click", () => loadDemo(true));
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-action=demo]"); if (t) loadDemo();
    const b = e.target.closest("[data-brief]");
    if (b) openViewer({ rec: state.records.find((r) => r.task_id === b.dataset.brief && r.action === "handoff_build") });
    const tr = e.target.closest("tbody tr"); if (tr) openViewer({ rec: state.records[+tr.dataset.i] });
  });
  $("#rows").addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches("tr")) { e.preventDefault(); openViewer({ rec: state.records[+e.target.dataset.i] }); }
  });
  $("#reload").addEventListener("click", loadLive);
  $("#q").addEventListener("input", renderRows);
  $("#act-filter").addEventListener("change", renderRows);
  $("#file").addEventListener("change", async (e) => {
    const f = e.target.files[0]; if (!f) return;
    const { records, errors } = parseJsonl(await f.text());
    if (!records.length && !errors.length) errors.push("The file is empty.");
    state = { records, briefs: {}, simulated: false, errors };
    setSource(f.name, "file");
    render(); e.target.value = "";
  });
  $("#open-brief").addEventListener("click", () => $("#brief-file").click());
  $("#brief-file").addEventListener("change", async (e) => {
    const f = e.target.files[0]; if (!f) return;
    openViewer({ markdown: await f.text(), name: f.name }); e.target.value = "";
  });
  $("#viewer-close").addEventListener("click", () => $("#viewer").close());
  $("#viewer").addEventListener("click", (e) => { if (e.target === $("#viewer")) $("#viewer").close(); });
  $("#toggle-raw").addEventListener("click", (e) => {
    const raw = $("#viewer-raw"), on = raw.hidden;
    raw.hidden = !on; $("#viewer-body").hidden = on;
    e.target.setAttribute("aria-pressed", String(on)); e.target.textContent = on ? "Show formatted" : "Show raw markdown";
  });
  $("#copy-cmd").addEventListener("click", async () => {
    const p = current?.rec?.extra?.handoff_path || (current?.rec ? `handoffs/${current.rec.task_id}.md` : "brief.md");
    const cmd = `grok -p "$(cat ${p})"`;
    try { await navigator.clipboard.writeText(cmd); $("#copy-status").textContent = "Copied: " + cmd; }
    catch { $("#copy-status").textContent = cmd; }
  });

  if (PROJECT_URL) {
    const a = document.createElement("a");
    a.href = PROJECT_URL + (PROJECT_URL.includes("?") ? "&" : "?") + "ref=dashboard";
    a.textContent = "Powered by JevGB";
    a.rel = "noopener";
    $("#powered").replaceChildren(a);
  }

  const params = new URLSearchParams(location.search);
  const ready = params.has("demo") ? Promise.resolve(loadDemo(false))
    : LIVE ? loadLive() : Promise.resolve((setSource("none", "none"), render()));
  ready.then(() => {
    if (!params.has("brief")) return;
    const r = state.records.find((x) => x.action === "handoff_build");
    if (r) openViewer({ rec: r });
  });
})();
