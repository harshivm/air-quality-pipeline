const pollutantSelect = document.getElementById("pollutantSelect");
const countryInput = document.getElementById("countryInput");
const cityInput = document.getElementById("cityInput");
const applyBtn = document.getElementById("applyBtn");
const resetBtn = document.getElementById("resetBtn");

const kpiRecords = document.getElementById("kpiRecords");
const kpiPollutants = document.getElementById("kpiPollutants");
const kpiCountries = document.getElementById("kpiCountries");

const pollutantBars = document.getElementById("pollutantBars");
const countryBars = document.getElementById("countryBars");
const recordsBody = document.getElementById("recordsBody");
const rowCount = document.getElementById("rowCount");

function makeBarRows(container, data, maxItems = 8) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]).slice(0, maxItems);
  const max = entries.length ? entries[0][1] : 1;

  container.innerHTML = "";
  for (const [label, value] of entries) {
    const width = Math.round((value / max) * 100);
    const row = document.createElement("div");
    row.className = "bar-item";
    row.innerHTML = `
      <span>${label}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span>
      <strong>${value}</strong>
    `;
    container.appendChild(row);
  }
}

function renderRecords(rows) {
  recordsBody.innerHTML = "";

  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.country_label || "-"}</td>
      <td>${row.city || "-"}</td>
      <td>${row.pollutant || "-"}</td>
      <td>${row.value ?? "-"}</td>
      <td>${row.unit || "-"}</td>
      <td>${row.last_updated ? new Date(row.last_updated).toLocaleString() : "-"}</td>
    `;
    recordsBody.appendChild(tr);
  }

  rowCount.textContent = `${rows.length} rows`;
}

function buildRecordsUrl() {
  const params = new URLSearchParams({ limit: "30" });
  if (pollutantSelect.value) params.set("pollutant", pollutantSelect.value);
  if (countryInput.value.trim()) params.set("country_code", countryInput.value.trim().toUpperCase());
  if (cityInput.value.trim()) params.set("city", cityInput.value.trim());
  return `/records?${params.toString()}`;
}

async function loadSummary() {
  const response = await fetch("/summary");
  const data = await response.json();

  kpiRecords.textContent = (data.total_records || 0).toLocaleString();
  kpiPollutants.textContent = Object.keys(data.pollutants || {}).length;
  kpiCountries.textContent = Object.keys(data.countries || {}).length;

  makeBarRows(pollutantBars, data.pollutants);
  makeBarRows(countryBars, data.countries);

  const pollutants = Object.keys(data.pollutants || {}).sort();
  pollutantSelect.innerHTML = '<option value="">All pollutants</option>';
  for (const pollutant of pollutants) {
    const option = document.createElement("option");
    option.value = pollutant;
    option.textContent = pollutant;
    pollutantSelect.appendChild(option);
  }
}

async function loadRecords() {
  const response = await fetch(buildRecordsUrl());
  const records = await response.json();
  renderRecords(records);
}

async function bootstrap() {
  try {
    await loadSummary();
    await loadRecords();
  } catch (error) {
    recordsBody.innerHTML = `<tr><td colspan="6">Failed to load dashboard data. ${error}</td></tr>`;
  }
}

applyBtn.addEventListener("click", loadRecords);
resetBtn.addEventListener("click", () => {
  pollutantSelect.value = "";
  countryInput.value = "";
  cityInput.value = "";
  loadRecords();
});

bootstrap();
