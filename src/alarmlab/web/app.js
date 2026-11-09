(function () {
  "use strict";
  const D = window.ALARMLAB_DATA;
  const $ = (id) => document.getElementById(id);
  const names = {
    contextual_residual: "Kontekstuell residualmodell",
    isolation_forest: "Isolation Forest", raw_limits: "Robuste sensorgrenser"
  };
  const scenarioNames = {
    normal: "Normal drift", load_step: "Legitimt lastskifte",
    pump_wear: "Pumpesvekkelse", cooling_loss: "Redusert kjøling",
    sensor_bias: "Sensorbias", dropout: "Manglende målinger",
    stuck_sensor: "Frosset sensor"
  };
  const sensorInfo = {
    temperature_c: ["Temperatur", "°C", "TT-01"],
    flow_lpm: ["Volumstrøm", "L/min", "FT-01"],
    pressure_bar: ["Trykk", "bar", "PT-01"],
    vibration_mm_s: ["Vibrasjon", "mm/s", "VT-01"]
  };
  const reasons = {
    missing_or_nonfinite: "En eller flere målinger mangler eller er ugyldige.",
    stuck_sensor: "En sensor har gjentatt nøyaktig samme måling over tid.",
    outside_physical_range: "En måling ligger utenfor de definerte fysiske grensene.",
    unsupported_context: "Driftsforholdene ligger utenfor området modellen er trent på."
  };
  let sensor = "temperature_c";
  let cursor = 350;
  let timer = null;
  let logEntries = [];
  try {
    const stored = JSON.parse(localStorage.getItem("alarmlab-log-v1") || "[]");
    if (Array.isArray(stored)) logEntries = stored.slice(-200);
  } catch (_) { /* Replay also works with disabled local storage. */ }
  const number = (x, digits = 2) => x == null || !Number.isFinite(x) ? "—" : x.toLocaleString("nb-NO", {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const percent = (x, digits = 0) => x == null ? "—" : number(x * 100, digits) + " %";
  const clock = (seconds) => String(Math.floor(seconds / 60)).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
  const trace = () => D.traces.find(t => t.scenario === $("scenario").value && t.domain === $("domain").value);
  const set = (id, text) => { $(id).textContent = text; };
  const escape = (value) => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
  const metricCard = (label, value, detail) => '<div class="metric-card"><span>' + escape(label) + '</span><strong>' + escape(value) + '</strong><small>' + escape(detail) + '</small></div>';
  const table = (headers, rows) => "<thead><tr>" + headers.map(h => "<th>" + escape(h) + "</th>").join("") + "</tr></thead><tbody>" + rows.map(r => '<tr class="' + (r.highlight ? "highlight" : "") + '">' + r.cells.map(c => "<td>" + escape(c) + "</td>").join("") + "</tr>").join("") + "</tbody>";

  function renderChart(id, series, options) {
    const svg = $(id), width = 800, height = options.height;
    const left = 48, right = 15, top = 14, bottom = 28;
    const plotW = width - left - right, plotH = height - top - bottom;
    const t = trace();
    const values = series.flatMap(s => s.values.slice(0, cursor + 1)).filter(v => v != null && Number.isFinite(v));
    if (options.threshold != null) values.push(options.threshold);
    let lo = values.length ? Math.min(...values) : 0;
    let hi = values.length ? Math.max(...values) : 1;
    const pad = Math.max((hi - lo) * 0.12, options.zero ? 0.12 : 0.08);
    lo = options.zero ? 0 : lo - pad;
    hi += pad;
    if (hi <= lo) hi = lo + 1;
    const X = (seconds) => left + seconds / t.t[t.t.length - 1] * plotW;
    const Y = (value) => top + (hi - value) / (hi - lo) * plotH;
    let markup = "<title>" + escape(options.title) + "</title>";
    const ticks = options.height > 150 ? 4 : 2;
    for (let k = 0; k <= ticks; k++) {
      const val = lo + (hi - lo) * k / ticks, py = Y(val);
      markup += '<path d="M' + left + " " + py + " H" + (width - right) + '" stroke="#c8c3b5" stroke-width="0.7"/>';
      markup += '<text x="' + (left - 8) + '" y="' + (py + 3) + '" text-anchor="end">' + number(val, options.zero ? 1 : 1) + "</text>";
    }
    for (let s = 0; s <= 1200; s += 240) {
      if (s > t.t[t.t.length - 1]) break;
      markup += '<text x="' + X(s) + '" y="' + (height - 7) + '" text-anchor="middle">' + clock(s) + "</text>";
    }
    if ($("truth").checked && t.onset >= 0 && t.onset <= t.t[cursor]) {
      markup += '<rect x="' + X(t.onset) + '" y="' + top + '" width="' + (X(t.t[cursor]) - X(t.onset)) + '" height="' + plotH + '" fill="#974720" opacity=".055"/>';
      markup += '<path d="M' + X(t.onset) + " " + top + " V" + (height - bottom) + '" stroke="#974720" stroke-dasharray="4 5" opacity=".55"/>';
    }
    if (options.threshold != null) {
      const yy = Y(options.threshold);
      markup += '<path d="M' + left + " " + yy + " H" + (width - right) + '" stroke="#974720" stroke-dasharray="5 6" opacity=".65"/>';
      markup += '<text x="' + (width - 16) + '" y="' + Math.max(10, yy - 5) + '" text-anchor="end">Terskel 1,0×</text>';
    }
    series.forEach(s => {
      let path = "", segment = false, last = null;
      s.values.slice(0, cursor + 1).forEach((v, i) => {
        if (v == null || !Number.isFinite(v)) { segment = false; return; }
        const x = X(t.t[i]), y = Y(v);
        path += (segment ? " L" : " M") + x.toFixed(2) + " " + y.toFixed(2);
        segment = true; last = {x, y, i};
      });
      markup += '<path d="' + path + '" stroke="' + s.color + '" stroke-width="1.8" fill="none"' + (s.dashed ? ' stroke-dasharray="6 5"' : "") + "/>";
      if (last && last.i === cursor) markup += '<circle cx="' + last.x + '" cy="' + last.y + '" r="3" fill="' + s.color + '"/>';
    });
    markup += '<path d="M' + X(t.t[cursor]) + " " + top + " V" + (height - bottom) + '" stroke="#777365" opacity=".4" stroke-dasharray="3 5"/>';
    svg.innerHTML = markup;
  }

  function renderOperator() {
    const t = trace(), method = $("model").value;
    cursor = Math.max(0, Math.min(cursor, t.t.length - 1));
    $("time").max = t.t.length - 1;
    $("time").value = cursor;
    const current = t.methods[method], status = current.states[cursor];
    const threshold = D.synthetic.model.thresholds[method];
    set("run-id", t.id.toUpperCase());
    set("heat-value", number(t.context.heat_kw[cursor], 1) + " kW");
    set("pump-value", number(t.context.pump_pct[cursor], 1) + " %");
    set("ambient-value", number(t.context.ambient_c[cursor], 1) + " °C");
    $("sensor-cards").innerHTML = Object.entries(sensorInfo).map(([key, info]) =>
      '<button class="sensor-card ' + (key === sensor ? "active" : "") + '" data-sensor="' + key + '" aria-pressed="' + (key === sensor) + '"><span class="sensor-name">' + info[0] + "</span><b>" + number(t.sensors[key][cursor], key === "vibration_mm_s" ? 2 : 1) + "</b><small>" + info[1] + '</small><span class="sensor-id">' + info[2] + "</span></button>"
    ).join("");
    $("sensor-cards").querySelectorAll("button").forEach(b => b.addEventListener("click", () => { sensor = b.dataset.sensor; renderOperator(); }));
    const statusText = {
      NORMAL: ["Ingen vedvarende avvik", "Målingene har ikke utløst en vedvarende alarm. Dette er ikke en garanti for feilfri drift.", "normal"],
      WATCH: ["Følg med", "Skåren overskrider terskelen, men har ennå ikke oppfylt kravet om tre sammenhengende overskridelser.", "alarm"],
      ALARM: ["Avvik — vurder signalene", "En vedvarende alarm er aktiv. Vurder trendene og datakvaliteten; modellen fastslår ikke feilårsaken.", "alarm"],
      REVIEW: ["Vurdering utilgjengelig", reasons[t.quality[cursor]] || "Datagrunnlaget er utilstrekkelig.", "review"],
      WARMUP: ["Bygger historikk", "De første 60 sekundene er oppvarming. Ingen alarmvurdering gis i dette tidsrommet.", "warmup"]
    }[status];
    $("status").className = "status " + statusText[2];
    $("status").querySelector("strong").textContent = statusText[0];
    set("status-copy", statusText[1]);
    set("tail-value", ["REVIEW", "WARMUP"].includes(status) ? "—" : number(current.tail[cursor], 4));
    set("signal-title", sensorInfo[sensor][0] + " · " + sensorInfo[sensor][1]);
    const expected = t.expected[sensor].map((value, i) => t.quality[i] ? null : value);
    renderChart("signal-chart", [
      {values: expected, color: "#405b82", dashed: true},
      {values: t.sensors[sensor], color: "#286756"}
    ], {height: 235, title: sensorInfo[sensor][0] + " frem til " + clock(t.t[cursor])});
    const ratios = current.scores.map((v, i) => v == null || current.states[i] === "WARMUP" ? null : v / threshold);
    renderChart("score-chart", [{values: ratios, color: "#974720"}], {height: 118, threshold: 1, zero: true, title: "Avviksskår delt på terskel"});
    set("score-value", ratios[cursor] == null ? "Ingen skår" : number(ratios[cursor], 2) + "× terskel");
    set("time-label", clock(t.t[cursor]));
    $("truth-caption").hidden = !$("truth").checked;
    set("truth-caption", t.onset >= 0 ? "Fasit: innført avvik fra " + clock(t.onset) + ". Fasiten brukes kun til evaluering, ikke som modellinput." : "Fasit: ingen innført feil. Lastskifter kan være legitim drift.");
    const ranked = Object.entries(sensorInfo).map(([s, info]) => ({name: info[0], value: t.residuals[s][cursor]})).sort((a, b) => (b.value || 0) - (a.value || 0));
    if (["REVIEW", "WARMUP"].includes(status)) {
      $("explanations").innerHTML = '<p class="muted">Ingen forklaring vises når modellen avstår fra vurdering.</p>';
    } else {
      const max = Math.max(1, ...ranked.map(r => r.value || 0));
      $("explanations").innerHTML = ranked.map(r => '<div class="explanation-row"><div class="explanation-label"><span>' + r.name + "</span><b>" + number(r.value, 1) + ' z</b></div><div class="bar-track"><div class="bar-fill" style="width:' + (100 * (r.value || 0) / max) + '%"></div></div></div>').join("");
    }
    set("explanation-note", method === "contextual_residual"
      ? "Absolutte residualer, skalert med normal variasjon. Dette beskriver avvik, ikke årsakssammenhenger."
      : "Avvik mot en separat referansemodell. Dette er ikke en forklaring av den valgte detektorens beslutning.");
  }

  function renderResults() {
    const domain = $("results-domain").value;
    const rows = D.synthetic.summary.filter(r => r.domain === domain);
    const main = rows.find(r => r.method === "contextual_residual");
    $("metrics").innerHTML = [
      metricCard("Residualmodell · hendelser oppdaget", main.detected_events + " / " + main.process_events, "Én ny alarm etter feilstart kreves"),
      metricCard("Falske alarmer per normaltime", number(main.false_alarms_per_hour), number(main.normal_monitored_hours, 1) + " timer med overvåket normaldrift"),
      metricCard("Median forsinkelse", main.median_delay_s_detected_only == null ? "—" : number(main.median_delay_s_detected_only, 0) + " s", "Kun blant oppdagede hendelser"),
      metricCard("Dekning", percent(main.coverage), "Tid med tilgjengelig modellvurdering")
    ].join("");
    $("results-table").innerHTML = table(
      ["Metode", "Hendelsesrecall", "95 % Wilson-intervall", "Falske / t", "Forsinkelse*", "Normal tid i alarm"],
      rows.map(r => ({highlight: r.method === "contextual_residual", cells: [
        names[r.method], percent(r.event_recall, 1), percent(r.event_recall_wilson95[0]) + "–" + percent(r.event_recall_wilson95[1]),
        number(r.false_alarms_per_hour), r.median_delay_s_detected_only == null ? "—" : number(r.median_delay_s_detected_only, 0) + " s", percent(r.normal_alarm_occupancy, 1)
      ]}))
    );
    const ab = D.synthetic.persistence_ablation.find(r => r.method === "contextual_residual" && r.domain === domain);
    $("ablation").innerHTML = '<div class="mini-stat"><span>Uten tidslogikk · falske alarmstarter</span><b>' + ab.without_persistence_false_starts + '</b></div><div class="mini-stat"><span>Med tidslogikk · falske alarmstarter</span><b>' + ab.with_persistence_false_starts + "</b></div>";
    $("scenario-table").innerHTML = table(
      ["Scenario", "Prosesshendelser", "Oppdaget", "Median forsinkelse*", "Datafeil oppdaget", "Dekning"],
      D.scenarios.filter(r => r.domain === domain && r.method === "contextual_residual").map(r => ({cells: [
        scenarioNames[r.scenario], r.events, r.detected, r.median_delay_s == null ? "—" : number(r.median_delay_s, 0) + " s",
        r.quality_events ? r.quality_detected + " / " + r.quality_events : "—", percent(r.coverage)
      ]}))
    );
  }

  function renderReal() {
    const r = D.real;
    $("real-metrics").innerHTML = [
      metricCard("Målte sykluser", number(r.rows, 0), "60 sekunder per syklus"),
      metricCard("Avledede egenskaper", r.features.length, "9 fysiske sensorer × 4 statistikker"),
      metricCard("Testsykluser", r.split_sizes.test, r.split_groups.test + " holdt-utenfor driftskombinasjoner"),
      metricCard("Uavhengige anlegg", "1", "Generalisering til nye anlegg er ikke testet")
    ].join("");
    $("real-table").innerHTML = table(
      ["Modell", "Balansert nøyaktighet", "95 % gruppebootstrap", "Makro F1", "ROC AUC", "TN / FP / FN / TP"],
      r.metrics.filter(m => m.split === "test" && m.task === $("real-task").value).map(m => ({highlight: m.model === "random_forest", cells: [
        {dummy_prior: "Referanse: klassefordeling", logistic_regression: "Logistisk regresjon", random_forest: "Random Forest"}[m.model],
        percent(m.balanced_accuracy, 1), percent(m.balanced_accuracy_group_bootstrap95[0], 1) + "–" + percent(m.balanced_accuracy_group_bootstrap95[1], 1),
        number(m.macro_f1, 3), number(m.roc_auc, 3), m.confusion_matrix_tn_fp_fn_tp.join(" / ")
      ]}))
    );
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    set("play", "Spill av");
  }
  ["scenario", "domain", "model"].forEach(id => $(id).addEventListener("change", () => { stop(); renderOperator(); }));
  $("time").addEventListener("input", () => { stop(); cursor = Number($("time").value); renderOperator(); });
  $("truth").addEventListener("change", renderOperator);
  $("restart").addEventListener("click", () => { stop(); cursor = 0; renderOperator(); });
  $("play").addEventListener("click", () => {
    if (timer) { stop(); return; }
    if (cursor >= trace().t.length - 1) cursor = 0;
    set("play", "Pause");
    timer = setInterval(() => {
      cursor += 2; renderOperator();
      if (cursor >= trace().t.length - 1) stop();
    }, 200);
  });
  document.querySelectorAll(".tab").forEach(button => button.addEventListener("click", () => {
    stop();
    document.querySelectorAll(".tab").forEach(b => { b.classList.toggle("active", b === button); b.setAttribute("aria-pressed", String(b === button)); });
    document.querySelectorAll(".view").forEach(v => { v.classList.toggle("active", v.id === button.dataset.tab); v.hidden = v.id !== button.dataset.tab; });
    set("data-mode", button.dataset.tab === "real" ? "Målte data fra UCI 447 · separat klassifikasjonsoppgave · CC BY 4.0" : "Simulert, generisk kjølekrets · avspilling av beregnede modellresultater");
    if (button.dataset.tab === "results") renderResults();
    if (button.dataset.tab === "real") renderReal();
  }));
  $("results-domain").addEventListener("change", renderResults);
  $("real-task").addEventListener("change", renderReal);
  $("log").addEventListener("click", () => {
    const t = trace(), method = $("model").value;
    logEntries.push({
      recorded_at_utc: new Date().toISOString(), run_id: t.id,
      scenario: t.scenario, domain: t.domain, simulated_time_s: t.t[cursor],
      model: method, model_status: t.methods[method].states[cursor],
      score: t.methods[method].scores[cursor], quality_reason: t.quality[cursor],
      decision: $("decision").value, rationale: $("note").value.trim(),
      ground_truth_visible: $("truth").checked, predictions_sha256: D.predictions_sha256
    });
    logEntries = logEntries.slice(-200);
    let persisted = true;
    try { localStorage.setItem("alarmlab-log-v1", JSON.stringify(logEntries)); } catch (_) { persisted = false; }
    set("log-message", logEntries.length + " vurdering(er). " + (persisted ? "Lagret lokalt." : "Kun i minnet; eksporter før du lukker."));
    $("note").value = "";
  });
  $("export-log").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({schema: "alarmlab-study-log/1", entries: logEntries}, null, 2)], {type:"application/json"}));
    const link = document.createElement("a");
    link.href = url; link.download = "alarmlab-ovelseslogg.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  set("provenance", "Seed " + D.manifest.config.seed + " · " + D.manifest.episodes + " simulerte kjøringer · Python " + D.manifest.python + " · SHA-256 prediksjoner: " + D.predictions_sha256);
  if (logEntries.length) set("log-message", logEntries.length + " vurdering(er) lagret i nettleseren.");
  renderOperator(); renderResults(); renderReal();
})();
