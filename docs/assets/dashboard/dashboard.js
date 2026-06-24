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

const siteDescriptions = {
  1: "A greener, lower-density refuge area. It has lower exposure, so even when heat hours appear in the future, the overall risk score stays low.",
  2: "A greener refuge neighbourhood with relatively low daytime population. It remains one of the lower-risk places in the city.",
  3: "A refuge neighbourhood with low exposure but slightly higher sensitivity than the other refuge sites. Future heat rises, but risk remains low because fewer people are exposed.",
  4: "A dense hotspot with high daytime population, low access to cooling and many outdoor workers. Heat translates into high social risk here.",
  5: "A dense hotspot with sparse green cover and high social vulnerability. It is one of the places where heat reductions would matter most.",
  6: "A core business and civic area with substantial daytime population but lower sensitivity. It becomes risky when heat crosses the 35 C threshold.",
  7: "A dense hotspot with the highest sensitivity score in the dataset. It is consistently one of the top priorities for heat action.",
  8: "A core commercial area with high daytime exposure but lower sensitivity. It has moderate future risk compared with the hotspots.",
  9: "The highest-risk neighbourhood in the future run. It combines the most heat hours with high exposure and high sensitivity.",
  10: "A dense core area with high buildings and substantial daytime activity, but low measured sensitivity in the synthetic data, so the risk score stays low.",
};

const plainExperimentLabels = {
  "Trees +5pp": "More tree cover (+5 points)",
  "Trees +10pp": "More tree cover (+10 points)",
  "Paved albedo 0.35": "Cooler paving",
  "Building albedo 0.35": "Cooler roofs and buildings",
  "Grass +5pp": "More grass (+5 points)",
  "Water +2pp": "More water (+2 points)",
  "Evergreen irrigation": "Water evergreen trees",
  "Vegetation soil store 300": "More soil water storage",
};

const plainExperimentParameters = {
  "trees_5pp_from_paved": "Shift 5 percentage points from paved surface to evergreen tree cover.",
  "trees_10pp_from_paved": "Shift 10 percentage points from paved surface to evergreen tree cover.",
  "paved_albedo_035": "Make paved surfaces more reflective: 0.20 to 0.35.",
  "building_albedo_035": "Make roofs and building surfaces more reflective: 0.20 to 0.35.",
  "grass_5pp_from_paved": "Shift 5 percentage points from paved surface to grass.",
  "water_2pp_from_paved": "Shift 2 percentage points from paved surface to water.",
  "evetr_irrigation_fraction_100": "Assume evergreen trees are fully irrigated.",
  "vegetation_soil_store_300": "Double vegetation soil-water storage from 150 to 300.",
};

const plainGroupLabels = {
  "Vegetation cover": "Trees and grass",
  Albedo: "Reflective surfaces",
  "Water and hydrology": "Water",
};

const experimentLabel = (experiment) =>
  plainExperimentLabels[experiment.label] || experiment.label;

const experimentParameter = (experiment) =>
  plainExperimentParameters[experiment.id] || experiment.parameter;

const experimentGroup = (group) => plainGroupLabels[group] || group;

function renderSummary() {
  byId("top-risk-site").textContent = data.summary.topFutureRiskSite;
  byId("top-risk-detail").textContent = `${data.summary.topFutureHours} future heat hours, risk score ${data.summary.topFutureRisk.toFixed(2)}`;
  byId("future-mean-hours").textContent = `${data.summary.futureMeanHours}`;
  byId("best-experiment").textContent = plainExperimentLabels[data.summary.bestExperiment] || data.summary.bestExperiment;
  byId("best-experiment-detail").textContent = `${formatSigned(data.summary.bestExperimentDelta)} average heat hours`;
  byId("worst-experiment").textContent = plainExperimentLabels[data.summary.worstExperiment] || data.summary.worstExperiment;
  byId("worst-experiment-detail").textContent = `${formatSigned(data.summary.worstExperimentDelta)} average heat hours`;
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
    .map((group, index) => `<button type="button" class="${index === 0 ? "active" : ""}" data-group="${group}">${group === "All" ? "All" : experimentGroup(group)}</button>`)
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
        <td><strong>${experimentLabel(experiment)}</strong><br><small>${experiment.note}</small></td>
        <td>${experimentGroup(experiment.group)}</td>
        <td>${experimentParameter(experiment)}</td>
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
    ["Heat", site.hazard],
    ["People exposed", site.exposure],
    ["Sensitivity", site.vulnerability],
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
  byId("site-risk").textContent = `Risk score ${site.futureRisk.toFixed(2)} #${site.futureRank}`;
  byId("site-description").textContent = siteDescriptions[site.gridiv] || "";
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
      experimentData: data.experiments.find((experiment) => experiment.id === row.experiment),
    }))
    .sort((a, b) => a.deltaHours - b.deltaHours);

  byId("site-experiment-table").querySelector("tbody").innerHTML = rows
    .map((row) => `
      <tr>
        <td><strong>${row.experimentData ? experimentLabel(row.experimentData) : row.experiment}</strong></td>
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
