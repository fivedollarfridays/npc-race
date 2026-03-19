// Telemetry panel — Sprint 8 T8.4
// ── State ────────────────────────────────────────────────────────────────────
let _panelCar = null;
let _sectorBests = {};
let _sessionBestSectors = [Infinity, Infinity, Infinity];
let _alerts = [];
let _prevCarData = null;

// ── Init ─────────────────────────────────────────────────────────────────────
function initTelemetryPanel(replay) {
  const panel = document.getElementById('liveReadouts');
  if (!panel) return;

  panel.innerHTML = `
    <div class="readout"><span class="ro-label">Speed</span><span id="roSpeed" class="ro-value">---</span><span class="ro-unit">km/h</span></div>
    <div class="readout"><span class="ro-label">Tire</span><span id="roTireBar" class="ro-bar"><span class="bar-fill"></span></span><span id="roTireVal" class="ro-value">---%</span><span id="roCompound" class="ro-tag">MED</span><span id="roTireAge" class="ro-small">--L</span></div>
    <div class="readout"><span class="ro-label">Temp</span><span id="roTemp" class="ro-value">---°C</span><span id="roTempStatus" class="ro-tag">---</span></div>
    <div class="readout"><span class="ro-label">Fuel</span><span id="roFuelBar" class="ro-bar"><span class="bar-fill fuel"></span></span><span id="roFuelVal" class="ro-value">---%</span></div>
    <div class="readout"><span class="ro-label">DRS</span><span id="roDRS" class="ro-value">---</span></div>
    <div class="readout"><span class="ro-label">Engine</span><span id="roEngine" class="ro-value">---</span></div>
    <div class="readout"><span class="ro-label">Dirty Air</span><span id="roDirtyBar" class="ro-bar"><span class="bar-fill dirty"></span></span><span id="roDirtyVal" class="ro-value">---</span></div>
    <div class="readout"><span class="ro-label">Gap ▲</span><span id="roGapAhead" class="ro-value">---</span></div>
    <div class="readout"><span class="ro-label">Gap ▼</span><span id="roGapBehind" class="ro-value">---</span></div>
    <div class="readout"><span class="ro-label">Pit Stops</span><span id="roPitStops" class="ro-value">---</span></div>
  `;

  const sectorDiv = document.getElementById('sectorComparison');
  if (sectorDiv) {
    sectorDiv.innerHTML = `
      <div class="sector-header">SECTORS</div>
      <div class="sector-row"><span class="sector-label">S1</span><span id="secS1Time" class="sector-time">---</span><span id="secS1Delta" class="sector-delta">---</span></div>
      <div class="sector-row"><span class="sector-label">S2</span><span id="secS2Time" class="sector-time">---</span><span id="secS2Delta" class="sector-delta">---</span></div>
      <div class="sector-row"><span class="sector-label">S3</span><span id="secS3Time" class="sector-time">---</span><span id="secS3Delta" class="sector-delta">---</span></div>
      <div class="sector-row sector-lap"><span class="sector-label">Lap</span><span id="secLapTime" class="sector-time">---</span><span id="secLapDelta" class="sector-delta">---</span></div>
    `;
  }

  _sectorBests = {};
  _sessionBestSectors = [Infinity, Infinity, Infinity];
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setTextColor(id, text, cssVar) {
  const el = document.getElementById(id);
  if (el) { el.textContent = text; el.style.color = `var(${cssVar})`; }
}

function setBar(parentId, fraction, colorVar) {
  const parent = document.getElementById(parentId);
  if (!parent) return;
  const fill = parent.querySelector('.bar-fill');
  if (fill) {
    fill.style.width = `${Math.max(0, Math.min(100, fraction * 100))}%`;
    fill.style.background = `var(${colorVar})`;
  }
}

// ── Update ───────────────────────────────────────────────────────────────────
function updateTelemetryPanel(carData, prevCarData, allCars) {
  if (!carData) return;

  const nameEl = document.getElementById('selectedCarName');
  const colorEl = document.getElementById('selectedCarColor');
  if (nameEl) nameEl.textContent = carData.name;
  if (colorEl) colorEl.style.background = carData.color;

  setText('roSpeed', Math.round(carData.speed));

  // Tire wear bar + value
  const wearPct = Math.round((1 - carData.tire_wear) * 100);
  setText('roTireVal', `${wearPct}%`);
  setBar('roTireBar', 1 - carData.tire_wear,
    carData.tire_wear > 0.75 ? '--accent-red' : carData.tire_wear > 0.5 ? '--accent-yellow' : '--accent-green');

  // Compound + age
  const compNames = {soft: 'SOFT', medium: 'MED', hard: 'HARD'};
  const compColors = {soft: '--accent-red', medium: '--accent-yellow', hard: '--text-primary'};
  const comp = carData.tire_compound || 'medium';
  setTextColor('roCompound', compNames[comp] || 'MED', compColors[comp]);
  setText('roTireAge', `${carData.tire_age_laps || 0}L`);

  // Temp with optimal window
  const temp = carData.tire_temp || 20;
  setText('roTemp', `${temp.toFixed(0)}\u00B0C`);
  const optTemps = {soft: 90, medium: 80, hard: 70};
  const winTemps = {soft: 20, medium: 25, hard: 30};
  const opt = optTemps[comp] || 80;
  const win = winTemps[comp] || 25;
  const tempStatus = (temp >= opt - win && temp <= opt + win) ? 'OPTIMAL' :
                     (temp < opt - win) ? 'COLD' : 'HOT';
  const tempColor = tempStatus === 'OPTIMAL' ? '--accent-green' :
                    tempStatus === 'COLD' ? '--accent-blue' : '--accent-red';
  setTextColor('roTempStatus', tempStatus, tempColor);

  // Fuel
  const fuelPct = Math.round((carData.fuel_pct || 0) * 100);
  setText('roFuelVal', `${fuelPct}%`);
  setBar('roFuelBar', carData.fuel_pct || 0, '--accent-blue');

  // DRS
  const drsText = carData.drs_active ? 'ACTIVE' : 'READY';
  const drsColor = carData.drs_active ? '--accent-green' : '--text-secondary';
  setTextColor('roDRS', drsText, drsColor);

  // Engine mode
  const modeColors = {push: '--accent-red', standard: '--text-primary', conserve: '--accent-blue'};
  setTextColor('roEngine', (carData.engine_mode || 'standard').toUpperCase(),
    modeColors[carData.engine_mode] || '--text-primary');

  // Dirty air
  const dirtyFactor = carData.dirty_air_factor || 1.0;
  const isDirty = carData.in_dirty_air;
  setText('roDirtyVal', dirtyFactor.toFixed(3));
  setBar('roDirtyBar', dirtyFactor, isDirty ? '--accent-orange' : '--text-muted');

  // Gaps
  setText('roGapAhead', carData.gap_ahead_s ? `+${carData.gap_ahead_s.toFixed(3)}s` : '---');
  setText('roGapBehind', carData.gap_behind_s ? `-${carData.gap_behind_s.toFixed(3)}s` : '---');

  // Pit stops
  setText('roPitStops', String(carData.pit_stops || 0));

  // Sector tracking
  if (carData.last_sector_time != null && carData.last_sector_idx != null) {
    updateSectorData(carData);
  }

  // Last lap time
  if (carData.last_lap_time != null) {
    const lt = carData.last_lap_time;
    const m = Math.floor(lt / 60);
    const s = lt % 60;
    setText('secLapTime', `${m}:${s.toFixed(3).padStart(6, '0')}`);
    if (carData.best_lap_s) {
      const delta = lt - carData.best_lap_s;
      const deltaStr = delta >= 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3);
      setTextColor('secLapDelta', deltaStr,
        delta <= 0 ? '--accent-green' : '--accent-yellow');
    }
  }

  checkAlerts(carData, prevCarData);
  _prevCarData = carData;
}

// ── Sector tracking ──────────────────────────────────────────────────────────
function updateSectorData(carData) {
  const idx = carData.last_sector_idx;
  const time = carData.last_sector_time;
  if (idx == null || idx < 0 || idx > 2 || time == null) return;

  const name = carData.name;
  if (!_sectorBests[name]) _sectorBests[name] = [Infinity, Infinity, Infinity];

  const elTime = document.getElementById(`secS${idx + 1}Time`);
  const elDelta = document.getElementById(`secS${idx + 1}Delta`);
  if (!elTime || !elDelta) return;

  const m = Math.floor(time / 60);
  const s = time % 60;
  elTime.textContent = m > 0 ? `${m}:${s.toFixed(3).padStart(6, '0')}` : s.toFixed(3);

  const personalBest = _sectorBests[name][idx];
  const sessionBest = _sessionBestSectors[idx];

  let color = '--accent-yellow';
  if (time < sessionBest) {
    color = '--accent-purple';
    _sessionBestSectors[idx] = time;
  } else if (time < personalBest) {
    color = '--accent-green';
  }

  if (personalBest < Infinity) {
    const delta = time - personalBest;
    const deltaStr = delta >= 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3);
    elDelta.textContent = deltaStr;
    elDelta.style.color = `var(${color})`;
  }

  _sectorBests[name][idx] = Math.min(personalBest, time);
}

// ── Alert system ─────────────────────────────────────────────────────────────
function checkAlerts(car, prev) {
  const panel = document.getElementById('alertsPanel');
  if (!panel) return;

  if (car.in_dirty_air && prev && !prev.in_dirty_air) {
    pushAlert('warning', `DIRTY AIR: -${((1 - car.dirty_air_factor) * 100).toFixed(1)}% grip`);
  }

  if (car.tire_wear > 0.75 && (!prev || prev.tire_wear <= 0.75)) {
    pushAlert('danger', `TIRE CLIFF: Wear at ${(car.tire_wear * 100).toFixed(0)}%`);
  }

  if (prev && car.pit_status === 'racing' && prev.pit_status !== 'racing') {
    if (car.position < prev.position) {
      pushAlert('success', `UNDERCUT: Gained +${prev.position - car.position} position(s)`);
    } else if (car.position > prev.position) {
      pushAlert('danger', `OVERCUT: Lost -${car.position - prev.position} position(s)`);
    }
  }

  if (car.fuel_pct < 0.10 && (!prev || prev.fuel_pct >= 0.10)) {
    pushAlert('danger', 'FUEL CRITICAL: <10% remaining');
  }
}

function pushAlert(type, message) {
  const panel = document.getElementById('alertsPanel');
  if (!panel) return;

  const alertEl = document.createElement('div');
  alertEl.className = `alert alert-${type}`;
  const icon = type === 'success' ? '\u2713' : '\u26A0';
  alertEl.textContent = `${icon} ${message}`;
  panel.prepend(alertEl);

  while (panel.children.length > 3) {
    panel.removeChild(panel.lastChild);
  }

  setTimeout(() => { if (alertEl.parentNode) alertEl.remove(); }, 5000);
}

// ── Car selection listener ───────────────────────────────────────────────────
document.addEventListener('car-selected', (e) => {
  _panelCar = e.detail.name;
  _prevCarData = null;
  ['secS1Time', 'secS2Time', 'secS3Time', 'secLapTime'].forEach(id => setText(id, '---'));
  ['secS1Delta', 'secS2Delta', 'secS3Delta', 'secLapDelta'].forEach(id => setText(id, '---'));
});
