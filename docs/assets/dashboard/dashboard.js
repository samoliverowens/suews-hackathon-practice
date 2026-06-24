const data = window.DASHBOARD_DATA;

const formatSigned = (value, digits = 1) => {
  const fixed = Number(value).toFixed(digits);
  return Number(value) > 0 ? `+${fixed}` : fixed;
};

const formatIntSigned = (value) => {
  const rounded = Math.round(Number(value));
  return rounded > 0 ? `+${rounded}` : `${rounded}`;
};

const deltaClass = (value) => {
  if (value < 0) return "good";
  if (value > 0) return "bad";
  return "neutral";
};

const byId = (id) => document.getElementById(id);

function renderSummary() {
  byId("top-risk-site").textContent = data.summary.topFutureRiskSite;
  byId("top-risk-detail").textContent = `${data.summary.topFutureHours} future heat hours, risk ${data.summary.topFutureRisk.toFixed(2)}`;
  byId("future-mean-hours").textContent = `${data.summary.futureMeanHours}`;
  byId("best-experiment").textContent = data.summary.bestExperiment;
  byId("best-experiment-detail").textContent = `${formatSigned(data.summary.bestExperimentDelta)} mean hours`;
  byId("worst-experiment").textContent = data.summary.worstExperiment;
  byId("worst-experiment-detail").textContent = `${formatSigned(data.summary.worstExperimentDelta)} mean hours`;
  byId("compatibility-note").textContent = data.metadata.compatibilityNote;
}

function renderBaselineBars() {
  const maxHours = Math.max(...data.sites.map((site) => site.futureHours));
  byId("baseline-bars").innerHTML = data.sites
    .slice()
    .sort((a, b) => b.futureHours - a.futureHours)
    .map((site) => {
      const width = Math.max(2, (site.futureHours / maxHours) * 100);
      return `
        <div class="bar-row">
          <span class="bar-label">${site.name}</span>
          <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${width}%"></span></span>
          <strong class="number">${site.futureHours}</strong>
        </div>
      `;
    })
    .join("");
}

function renderFilters() {
  const groups = ["All", ...new Set(data.experiments.map((experiment) => experiment.group))];
  const filters = byId("experiment-filters");
  filters.innerHTML = groups
    .map((group, index) => `<button type="button" class="${index === 0 ? "active" : ""}" data-group="${group}">${group}</button>`)
    .join("");
  filters.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    filters.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    renderExperimentTable(button.dataset.group);
  });
}

function renderExperimentTable(group = "All") {
  const rows = data.experiments
    .filter((experiment) => group === "All" || experiment.group === group)
    .slice()
    .sort((a, b) => a.meanDeltaHours - b.meanDeltaHours);

  byId("experiment-table").querySelector("tbody").innerHTML = rows
    .map((experiment) => `
      <tr>
        <td><strong>${experiment.label}</strong><br><small>${experiment.note}</small></td>
        <td>${experiment.group}</td>
        <td>${experiment.parameter}</td>
        <td class="number">${experiment.baselineMeanHours.toFixed(1)}</td>
        <td class="number">${experiment.scenarioMeanHours.toFixed(1)}</td>
        <td class="number"><span class="delta ${deltaClass(experiment.meanDeltaHours)}">${formatSigned(experiment.meanDeltaHours)}</span></td>
        <td class="number">${formatIntSigned(experiment.minDeltaHours)} to ${formatIntSigned(experiment.maxDeltaHours)}</td>
      </tr>
    `)
    .join("");
}

function renderSitePicker() {
  const select = byId("site-select");
  select.innerHTML = data.sites
    .map((site) => `<option value="${site.gridiv}">${site.gridiv}. ${site.name}</option>`)
    .join("");
  select.addEventListener("change", () => renderSite(Number(select.value)));
  renderSite(data.sites[0].gridiv);
}

function renderComponents(site) {
  const components = [
    ["Hazard", site.hazard],
    ["Exposure", site.exposure],
    ["Vulnerability", site.vulnerability],
  ];
  byId("site-components").innerHTML = components
    .map(([label, value]) => `
      <div class="component-row">
        <span>${label}</span>
        <span class="bar-track" aria-hidden="true"><span class="component-fill" style="width:${Math.max(2, value * 100)}%"></span></span>
        <strong>${value.toFixed(2)}</strong>
      </div>
    `)
    .join("");
}

function renderSite(gridiv) {
  const site = data.sites.find((item) => item.gridiv === gridiv);
  if (!site) return;
  byId("site-name").textContent = site.name;
  byId("site-type").textContent = site.type;
  byId("site-risk").textContent = `Risk ${site.futureRisk.toFixed(2)} #${site.futureRank}`;
  byId("site-present-hours").textContent = site.presentHours;
  byId("site-future-hours").textContent = `${site.futureHours} (${formatIntSigned(site.deltaHours)})`;
  byId("site-t2").textContent = `${site.t2MeanFuture.toFixed(2)} C`;
  byId("site-flux").textContent = `${site.qhFuture.toFixed(1)} / ${site.qeFuture.toFixed(1)} W m-2`;
  const image = byId("site-image");
  image.src = site.image;
  image.alt = `${site.name} SUEWS and risk plot`;
  renderComponents(site);
  renderSiteExperimentTable(gridiv);
}

function renderSiteExperimentTable(gridiv) {
  const rows = (data.siteExperiments[String(gridiv)] || [])
    .map((row) => ({
      ...row,
      label: data.experiments.find((experiment) => experiment.id === row.experiment)?.label || row.experiment,
    }))
    .sort((a, b) => a.deltaHours - b.deltaHours);

  byId("site-experiment-table").querySelector("tbody").innerHTML = rows
    .map((row) => `
      <tr>
        <td><strong>${row.label}</strong></td>
        <td class="number">${row.baselineHours}</td>
        <td class="number">${row.scenarioHours}</td>
        <td class="number"><span class="delta ${deltaClass(row.deltaHours)}">${formatIntSigned(row.deltaHours)}</span></td>
        <td class="number">${formatSigned(row.deltaRisk, 3)}</td>
      </tr>
    `)
    .join("");
}

renderSummary();
renderBaselineBars();
renderFilters();
renderExperimentTable();
renderSitePicker();
