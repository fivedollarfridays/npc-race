// Post-race diagnostic mode — Sprint 8 T8.6
// Full-race analysis for the player's car, shown after race completion.

let _diagnosticActive = false;
let _playerCarName = null;

// ─── Init ────────────────────────────────────────────────────────────────────

function initDiagnostic(replay, playerCarName) {
  _playerCarName = playerCarName;
  _diagnosticActive = false;

  const statusBar = document.getElementById('statusBar');
  if (statusBar && !document.getElementById('diagnosticBtn')) {
    const btn = document.createElement('button');
    btn.id = 'diagnosticBtn';
    btn.textContent = 'DIAGNOSTIC';
    btn.style.display = 'none';
    btn.className = 'diag-btn';
    btn.addEventListener('click', () => toggleDiagnostic(replay));
    statusBar.appendChild(btn);
  }
}

// ─── Toggle ──────────────────────────────────────────────────────────────────

function toggleDiagnostic(replay) {
  if (!_playerCarName || !replay) return;
  _diagnosticActive = !_diagnosticActive;

  const btn = document.getElementById('diagnosticBtn');

  if (_diagnosticActive) {
    btn.textContent = 'LIVE VIEW';
    btn.classList.add('active');
    showDiagnostic(replay, _playerCarName);
  } else {
    btn.textContent = 'DIAGNOSTIC';
    btn.classList.remove('active');
    hideDiagnostic();
  }
}

// ─── Show diagnostic view ────────────────────────────────────────────────────

function showDiagnostic(replay, carName) {
  const strip = document.getElementById('telemetryStrip');
  if (!strip) return;

  strip._savedHTML = strip.innerHTML;

  strip.innerHTML = `
    <div id="diagContainer" style="display: flex; height: 100%; overflow: hidden;">
      <div id="diagLapChart" style="flex: 1; padding: 4px;">
        <canvas id="lapTimeCanvas"></canvas>
      </div>
      <div id="diagSectorTable" style="width: 400px; overflow-y: auto; padding: 4px; font-size: 10px;">
        <table id="sectorTable" class="diag-table"></table>
      </div>
    </div>
  `;

  const results = replay.results ? replay.results.find(r => r.name === carName) : null;
  if (!results) return;

  const lapTimes = results.lap_times || [];
  const bestLap = results.best_lap_s;

  drawLapTimeChart(lapTimes, bestLap, replay, carName);
  buildSectorTable(replay, carName, lapTimes);
}

// ─── Lap time bar chart ──────────────────────────────────────────────────────

function drawLapTimeChart(lapTimes, bestLap, replay, carName) {
  const canvas = document.getElementById('lapTimeCanvas');
  if (!canvas || lapTimes.length === 0) return;

  const container = canvas.parentElement;
  const dpr = window.devicePixelRatio || 1;
  const w = container.clientWidth;
  const h = container.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const maxTime = Math.max(...lapTimes) * 1.05;
  const barH = Math.min(20, (h - 20) / lapTimes.length);
  const labelW = 50;
  const chartW = w - labelW - 10;

  const compounds = getLapCompounds(replay, carName);
  const compColors = { soft: '#ef4444', medium: '#eab308', hard: '#e6edf3' };

  ctx.font = '10px JetBrains Mono';

  lapTimes.forEach((lt, i) => {
    const y = 10 + i * barH;
    const barW = (lt / maxTime) * chartW;
    const comp = compounds[i] || 'medium';

    // Bar fill
    ctx.fillStyle = compColors[comp] || '#eab308';
    ctx.globalAlpha = 0.7;
    ctx.fillRect(labelW, y, barW, barH - 2);
    ctx.globalAlpha = 1.0;

    // Best lap highlight
    if (bestLap && Math.abs(lt - bestLap) < 0.01) {
      ctx.strokeStyle = '#a855f7';
      ctx.lineWidth = 2;
      ctx.strokeRect(labelW, y, barW, barH - 2);
    }

    // Lap label
    ctx.fillStyle = '#8b949e';
    ctx.textAlign = 'right';
    ctx.fillText('L' + (i + 1), labelW - 6, y + barH - 5);

    // Time label
    ctx.fillStyle = '#e6edf3';
    ctx.textAlign = 'left';
    const m = Math.floor(lt / 60);
    const s = lt % 60;
    ctx.fillText(m + ':' + s.toFixed(3).padStart(6, '0'), labelW + barW + 4, y + barH - 5);
  });

  // Title
  ctx.fillStyle = '#484f58';
  ctx.textAlign = 'left';
  ctx.fillText('LAP TIMES', labelW, 8);
}

// ─── Scan replay for compound per lap ────────────────────────────────────────

function getLapCompounds(replay, carName) {
  const compounds = [];
  let prevLap = 0;
  let currentCompound = 'medium';

  for (const frameCars of replay.frames) {
    const car = frameCars.find(c => c.name === carName);
    if (!car) continue;
    if (car.lap > prevLap && prevLap >= 0) {
      compounds.push(currentCompound);
      prevLap = car.lap;
    }
    currentCompound = car.tire_compound || 'medium';
  }
  compounds.push(currentCompound);

  return compounds;
}

// ─── Sector breakdown table ──────────────────────────────────────────────────

function buildSectorTable(replay, carName, lapTimes) {
  const table = document.getElementById('sectorTable');
  if (!table) return;

  table.innerHTML = `
    <thead>
      <tr>
        <th>Lap</th><th>S1</th><th>S2</th><th>S3</th><th>Total</th><th>Comp</th>
      </tr>
    </thead>
    <tbody id="sectorBody"></tbody>
  `;

  const body = document.getElementById('sectorBody');
  const compounds = getLapCompounds(replay, carName);
  const compDots = { soft: '\uD83D\uDD34', medium: '\uD83D\uDFE1', hard: '\u26AA' };
  const minLap = Math.min(...lapTimes);

  lapTimes.forEach((lt, i) => {
    const m = Math.floor(lt / 60);
    const s = lt % 60;
    const timeStr = m + ':' + s.toFixed(3).padStart(6, '0');
    const isBest = Math.abs(lt - minLap) < 0.001;

    const row = document.createElement('tr');
    row.className = isBest ? 'diag-best' : '';
    row.innerHTML =
      '<td>L' + (i + 1) + '</td>' +
      '<td>--</td><td>--</td><td>--</td>' +
      '<td class="' + (isBest ? 'purple' : '') + '">' + timeStr + '</td>' +
      '<td>' + (compDots[compounds[i]] || '\uD83D\uDFE1') + '</td>';
    body.appendChild(row);
  });
}

// ─── Hide diagnostic, restore telemetry strip ────────────────────────────────

function hideDiagnostic() {
  const strip = document.getElementById('telemetryStrip');
  if (strip && strip._savedHTML) {
    strip.innerHTML = strip._savedHTML;
    if (typeof initTelemetryStrip === 'function' && typeof replay !== 'undefined' && replay) {
      initTelemetryStrip(replay);
    }
  }
}

// ─── Car selection listener ──────────────────────────────────────────────────

document.addEventListener('car-selected', (e) => {
  const btn = document.getElementById('diagnosticBtn');
  if (btn && _diagnosticActive && typeof replay !== 'undefined') {
    toggleDiagnostic(replay);
  }
  if (btn && btn.style.display !== 'none') {
    btn.style.display = (e.detail.name === _playerCarName) ? 'inline-block' : 'none';
  }
});
