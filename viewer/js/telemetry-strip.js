// Telemetry strip — Sprint 8 T8.5
// Time-series charts: speed trace, tire trace, gap trace

// ── State ────────────────────────────────────────────────────────────────────
let _stripHistory = {};
let _stripCar = null;
const STRIP_WINDOW = 5000;
let _stripUpdateCounter = 0;

// ── Init ─────────────────────────────────────────────────────────────────────
function initTelemetryStrip(replay) {
  const strip = document.getElementById('telemetryStrip');
  if (!strip) return;

  const w = strip.clientWidth;
  const dpr = window.devicePixelRatio || 1;

  ['speedTrace', 'tireTrace', 'gapTrace'].forEach((id, idx) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    const h = idx === 0 ? 80 : 50;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
  });

  _stripHistory = {};
}

// ── Update (called every frame) ──────────────────────────────────────────────
function updateTelemetryStrip(carData, tick, replay) {
  if (!carData) return;

  const name = carData.name;
  if (!_stripHistory[name]) {
    _stripHistory[name] = {
      speed: [], tire_wear: [], tire_temp: [],
      gap: [], dirty: [], pit: [], sector: []
    };
  }

  const h = _stripHistory[name];
  h.speed.push(carData.speed || 0);
  h.tire_wear.push(carData.tire_wear || 0);
  h.tire_temp.push(carData.tire_temp || 20);
  h.gap.push(carData.gap_ahead_s || 0);
  h.dirty.push(carData.in_dirty_air ? 1 : 0);
  h.pit.push(carData.pit_status !== 'racing' ? 1 : 0);
  h.sector.push(carData.current_sector || 0);

  const maxLen = STRIP_WINDOW;
  Object.keys(h).forEach(k => {
    if (h[k].length > maxLen) h[k] = h[k].slice(-maxLen);
  });

  _stripUpdateCounter++;
  if (_stripUpdateCounter % 3 !== 0) return;

  drawSpeedTrace(h, replay);
  drawTireTrace(h);
  drawGapTrace(h);
}

// ── Shared line drawing utility ──────────────────────────────────────────────
function drawLine(ctx, data, yMin, yMax, w, h, color, lineWidth) {
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = (i / data.length) * w;
    const y = h - ((data[i] - yMin) / (yMax - yMin)) * h;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
}

// ── Speed trace ──────────────────────────────────────────────────────────────
function drawSpeedTrace(history, replay) {
  const canvas = document.getElementById('speedTrace');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width / (window.devicePixelRatio || 1);
  const h = canvas.height / (window.devicePixelRatio || 1);

  ctx.clearRect(0, 0, w, h);

  const data = history.speed;
  if (data.length < 2) return;

  const yMin = 0;
  var maxSpeed = 100;
  for (var si = 0; si < data.length; si++) {
    if (data[si] > maxSpeed) maxSpeed = data[si];
  }
  const yMax = Math.max(maxSpeed * 1.1, 100);

  // Sector boundary lines
  const sectorData = history.sector;
  let prevSector = -1;
  for (let i = 0; i < sectorData.length; i++) {
    if (sectorData[i] !== prevSector) {
      const x = (i / data.length) * w;
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      ctx.setLineDash([2, 4]);
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
      ctx.setLineDash([]);
      prevSector = sectorData[i];
    }
  }

  // Dirty air zones (orange background)
  ctx.fillStyle = 'rgba(249, 115, 22, 0.1)';
  for (let i = 0; i < history.dirty.length; i++) {
    if (history.dirty[i]) {
      const x = (i / data.length) * w;
      ctx.fillRect(x, 0, Math.max(1, w / data.length), h);
    }
  }

  // Pit zones (red background)
  ctx.fillStyle = 'rgba(239, 68, 68, 0.15)';
  for (let i = 0; i < history.pit.length; i++) {
    if (history.pit[i]) {
      const x = (i / data.length) * w;
      ctx.fillRect(x, 0, Math.max(1, w / data.length), h);
    }
  }

  // Speed line
  drawLine(ctx, data, yMin, yMax, w, h, 'rgba(230, 237, 243, 0.9)', 1.5);

  // Y-axis labels
  ctx.fillStyle = 'rgba(139, 148, 158, 0.5)';
  ctx.font = '9px JetBrains Mono';
  ctx.fillText('370', 2, 12);
  ctx.fillText('0', 2, h - 2);

  // Label
  ctx.fillStyle = 'rgba(139, 148, 158, 0.3)';
  ctx.fillText('SPEED km/h', w - 80, 12);
}

// ── Tire trace (dual-axis: wear + temp) ──────────────────────────────────────
function drawTireTrace(history) {
  const canvas = document.getElementById('tireTrace');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width / (window.devicePixelRatio || 1);
  const h = canvas.height / (window.devicePixelRatio || 1);

  ctx.clearRect(0, 0, w, h);

  if (history.tire_wear.length < 2) return;

  // Wear line (green, scale 0-1)
  drawLine(ctx, history.tire_wear, 0, 1, w, h, 'rgba(34, 197, 94, 0.8)', 1.5);

  // Cliff threshold (red dashed at 0.78)
  const cliffY = h - (0.78 / 1.0) * h;
  ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(0, cliffY);
  ctx.lineTo(w, cliffY);
  ctx.stroke();
  ctx.setLineDash([]);

  // Temp line (orange, scale 20-150)
  drawLine(ctx, history.tire_temp, 20, 150, w, h, 'rgba(249, 115, 22, 0.8)', 1);

  // Labels
  ctx.fillStyle = 'rgba(139, 148, 158, 0.3)';
  ctx.font = '9px JetBrains Mono';
  ctx.fillText('WEAR', 2, 10);
  ctx.fillText('TEMP', w - 35, 10);
}

// ── Gap trace (green/red fill for gain/loss) ─────────────────────────────────
function drawGapTrace(history) {
  const canvas = document.getElementById('gapTrace');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width / (window.devicePixelRatio || 1);
  const h = canvas.height / (window.devicePixelRatio || 1);

  ctx.clearRect(0, 0, w, h);

  const data = history.gap;
  if (data.length < 2) return;

  const yMax = Math.max(10, Math.max(...data) * 1.2);

  // Fill: green when gap decreasing, red when increasing
  for (let i = 1; i < data.length; i++) {
    const x1 = ((i - 1) / data.length) * w;
    const x2 = (i / data.length) * w;
    const y1 = h - (data[i - 1] / yMax) * h;
    const y2 = h - (data[i] / yMax) * h;

    ctx.fillStyle = data[i] < data[i - 1]
      ? 'rgba(34, 197, 94, 0.15)'   // gaining (green)
      : 'rgba(239, 68, 68, 0.15)';  // losing (red)
    ctx.fillRect(x1, Math.min(y1, y2), x2 - x1, h - Math.min(y1, y2));
  }

  // Gap line
  drawLine(ctx, data, 0, yMax, w, h, 'rgba(230, 237, 243, 0.7)', 1);

  // Label
  ctx.fillStyle = 'rgba(139, 148, 158, 0.3)';
  ctx.font = '9px JetBrains Mono';
  ctx.fillText('GAP TO LEADER', 2, 10);
}

// ── Car selection listener ───────────────────────────────────────────────────
document.addEventListener('car-selected', (e) => {
  _stripCar = e.detail.name;
});
