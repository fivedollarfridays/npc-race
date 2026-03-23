// Code Terminal — Sprint 31 T31.3 + T31.4
// Shows part function calls synchronized with replay playback.
// Colors: green (ok), yellow (clamped), red (glitch/error)

let _terminalCar = null;
let _terminalEl = null;

function initCodeTerminal(replay) {
  _terminalEl = document.getElementById('codeTerminal');
  if (!_terminalEl) return;

  // Check if replay has call logs
  if (!replay.call_logs) {
    _terminalEl.innerHTML = '<div class="term-empty">No call log data in this replay</div>';
    return;
  }

  // Listen for car selection
  document.addEventListener('car-selected', (e) => {
    _terminalCar = e.detail?.name || null;
  });

  // Default to first car
  if (replay.results && replay.results.length > 0) {
    _terminalCar = replay.results[0].name;
  } else if (replay.frames && replay.frames.length > 0 && replay.frames[0].length > 0) {
    _terminalCar = replay.frames[0][0].name;
  }
}

function updateCodeTerminal(tick, replay) {
  if (!_terminalEl || !replay.call_logs || !_terminalCar) return;

  const carLogs = replay.call_logs[_terminalCar];
  if (!carLogs || carLogs.length === 0) return;

  // Find the closest sampled tick
  let closest = carLogs[0];
  for (const entry of carLogs) {
    if (entry.tick <= tick) closest = entry;
    else break;
  }

  // Grade card at the top
  const gradeHtml = renderCodeGrade(replay);

  // Render parts
  const html = closest.parts.map(p => {
    const statusClass = p.status === 'ok' ? 'term-ok'
      : p.status === 'clamped' ? 'term-clamped'
      : p.status === 'glitch' ? 'term-glitch' : 'term-error';
    const output = typeof p.output === 'object' ? JSON.stringify(p.output) : p.output;
    const statusBadge = p.status !== 'ok'
      ? `<span class="term-badge ${statusClass}">${p.status}</span>` : '';
    return `<div class="term-call ${statusClass}">` +
      `<span class="term-name">${p.name}()</span>` +
      `<span class="term-arrow">\u2192</span>` +
      `<span class="term-output">${output}</span>` +
      statusBadge +
      `</div>`;
  }).join('');

  _terminalEl.innerHTML =
    `<div class="term-header">${_terminalCar} \u00B7 tick ${closest.tick}</div>` +
    gradeHtml + html;
}

function renderCodeGrade(replay) {
  if (!replay.reliability || !_terminalCar) return '';

  const rel = replay.reliability[_terminalCar];
  if (rel === undefined) return '';

  const grade = rel >= 0.95 ? 'A' : rel >= 0.88 ? 'B' : rel >= 0.75 ? 'C' : 'D';
  const pct = Math.round(rel * 100);
  const barColor = rel >= 0.88 ? '#4caf50' : rel >= 0.75 ? '#ff9800' : '#f44336';

  return `<div class="grade-card">` +
    `<div class="grade-letter grade-${grade}">${grade}</div>` +
    `<div class="grade-bar"><div class="grade-fill" style="width:${pct}%;background:${barColor}"></div></div>` +
    `<div class="grade-pct">${pct}%</div>` +
    `</div>`;
}
