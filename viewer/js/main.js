// ─── State ──────────────────────────────────────────────────────────────────
let replay = null;
let frame = 0;
let playing = false;
let speed = 1;
let animId = null;
let lastTime = 0;
let accumulator = 0;

// Cached transform values (recomputed on resize / load)
let _scale = 1;
let _baseScale = 1;
let _ox = 0;
let _oy = 0;
let _rotation = 0;

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ─── Canvas refs ────────────────────────────────────────────────────────────
const bgCanvas = document.getElementById('trackBg');
const bgCtx = bgCanvas.getContext('2d');

const carCanvas = document.getElementById('carLayer');
const carCtx = carCanvas.getContext('2d');

const overlayCanvas = document.getElementById('overlayLayer');
const overlayCtx = overlayCanvas.getContext('2d');

// ─── File Loading ───────────────────────────────────────────────────────────
document.addEventListener('dragover', e => {
  e.preventDefault();
  document.getElementById('dropOverlay').style.display = 'flex';
});

document.addEventListener('dragleave', e => {
  if (e.relatedTarget === null) {
    document.getElementById('dropOverlay').style.display = 'none';
  }
});

document.addEventListener('drop', e => {
  e.preventDefault();
  document.getElementById('dropOverlay').style.display = 'none';
  const file = e.dataTransfer.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        loadReplay(JSON.parse(ev.target.result));
      } catch (err) {
        alert('Invalid replay file: ' + err.message);
      }
    };
    reader.readAsText(file);
  }
});

// Try loading replay.json from same directory
fetch('replay.json')
  .then(r => r.ok ? r.json() : null)
  .then(data => { if (data) loadReplay(data); })
  .catch(() => {});

function loadReplay(data) {
  replay = data;
  frame = 0;
  playing = false;

  enrichReplayData(replay);
  resetPhysicsFx();

  document.getElementById('noData').style.display = 'none';
  document.getElementById('finishedOverlay').style.display = 'none';
  document.getElementById('scrubber').max = replay.frames.length - 1;
  const trackLabel = replay.track_name ? esc(replay.track_name) : 'Procedural Track';
  document.getElementById('trackName').innerHTML =
    `<span class="track-label">\u25B6</span> ${trackLabel}`;
  document.getElementById('raceInfo').textContent =
    `${replay.car_count} cars \u00B7 ${replay.laps} laps \u00B7 ${replay.frames.length} frames`;

  resizeAllCanvases();
  computeTransform();
  renderBackground();
  render();
}

// ─── World-to-screen transform ──────────────────────────────────────────────
function computeTransform() {
  if (!replay) return;

  const w = bgCanvas.width / devicePixelRatio;
  const h = bgCanvas.height / devicePixelRatio;
  const track = replay.track;

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of track) {
    minX = Math.min(minX, p.x);
    minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x);
    maxY = Math.max(maxY, p.y);
  }

  const padding = 60;
  const tw = maxX - minX;
  const th = maxY - minY;
  _baseScale = Math.min((w - padding * 2) / tw, (h - padding * 2) / th);

  if (cameraSystem.mode !== 'full') {
    // Camera-based transform: center on camera position with zoom
    _scale = _baseScale * cameraSystem.currentZoom;
    _ox = w / 2 - cameraSystem.currentX * _scale;
    _oy = h / 2 - cameraSystem.currentY * _scale;
    _rotation = cameraSystem.currentRotation;
  } else {
    _scale = _baseScale;
    _ox = (w - tw * _scale) / 2 - minX * _scale;
    _oy = (h - th * _scale) / 2 - minY * _scale;
    _rotation = 0;
  }
}

function worldToScreen(wx, wy) {
  let sx = wx * _scale + _ox;
  let sy = wy * _scale + _oy;

  if (_rotation !== 0) {
    const w = bgCanvas.width / devicePixelRatio;
    const h = bgCanvas.height / devicePixelRatio;
    const cx = w / 2, cy = h / 2;
    const cos = Math.cos(_rotation);
    const sin = Math.sin(_rotation);
    const dx = sx - cx, dy = sy - cy;
    sx = cx + dx * cos - dy * sin;
    sy = cy + dx * sin + dy * cos;
  }

  return { x: sx, y: sy };
}

// ─── Canvas sizing ──────────────────────────────────────────────────────────
function resizeOneCanvas(cvs) {
  const container = cvs.parentElement;
  cvs.width = container.clientWidth * devicePixelRatio;
  cvs.height = container.clientHeight * devicePixelRatio;
  cvs.getContext('2d').setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
}

function resizeAllCanvases() {
  resizeOneCanvas(bgCanvas);
  resizeOneCanvas(carCanvas);
  resizeOneCanvas(overlayCanvas);
}

window.addEventListener('resize', () => {
  resizeAllCanvases();
  if (replay) {
    computeTransform();
    renderBackground();
    if (!playing) render();
  }
});

// ─── Background renderer (track surface) ────────────────────────────────────
function renderBackground() {
  const w = bgCanvas.width / devicePixelRatio;
  const h = bgCanvas.height / devicePixelRatio;
  bgCtx.clearRect(0, 0, w, h);

  if (!replay) return;
  computeTransform();
  renderTrack(bgCtx, replay, { scale: _scale, ox: _ox, oy: _oy, w, h });
  renderTireMarks(bgCtx, { scale: _scale, ox: _ox, oy: _oy });
}

// ─── Car renderer ───────────────────────────────────────────────────────────
function renderCars() {
  const w = carCanvas.width / devicePixelRatio;
  const h = carCanvas.height / devicePixelRatio;
  carCtx.clearRect(0, 0, w, h);
  if (!replay) return;

  const cars = replay.frames[frame];
  if (!cars) return;

  const prevCars = frame > 0 ? replay.frames[frame - 1] : null;
  const transform = { scale: _scale, ox: _ox, oy: _oy };

  // Update tire marks for this frame
  updateTireMarks(replay, frame, transform);

  // Sort so leader draws on top
  const sorted = [...cars].sort((a, b) => b.position - a.position);

  for (const car of sorted) {
    const prevCar = prevCars ? prevCars.find(c => c.name === car.name) : null;

    // Brake glow behind the car (drawn before car body)
    const heading = (replay.track_headings && car.seg != null)
      ? replay.track_headings[car.seg % replay.track_headings.length] : 0;
    const pos = worldToScreen(car.x, car.y);
    renderBrakeGlow(carCtx, car, prevCar, pos.x, pos.y, heading, _scale);

    renderCar(carCtx, car, prevCar, replay, transform);
  }

  // Drafting wake between close cars
  renderDraftingWake(carCtx, cars, replay, transform);
}

// ─── Overlay renderer (HUD / leaderboard) ───────────────────────────────────
function renderOverlay() {
  if (!replay) return;

  const w = overlayCanvas.width / devicePixelRatio;
  const h = overlayCanvas.height / devicePixelRatio;
  overlayCtx.clearRect(0, 0, w, h);

  const cars = replay.frames[frame];
  if (!cars) return;

  // Canvas broadcast overlay
  renderBroadcastOverlay(overlayCtx, replay, frame, w, h);

  document.getElementById('scrubber').value = frame;

  if (frame >= replay.frames.length - 1 && replay.results) {
    showResults();
  }
}

// ─── Main render (per-frame) ────────────────────────────────────────────────
function render() {
  if (!replay) return;
  renderCars();
  renderOverlay();
}

function showResults() {
  if (!replay.results) return;
  const overlay = document.getElementById('finishedOverlay');
  overlay.style.display = 'block';

  overlay.innerHTML = `<h2>🏁 <span>RACE COMPLETE</span></h2>` +
    replay.results.map(r => `
      <div class="result-row">
        <div class="result-pos" style="color:${r.position === 1 ? '#ffd700' : r.position === 2 ? '#c0c0c0' : r.position === 3 ? '#cd7f32' : '#888'}">
          P${r.position}
        </div>
        <div class="result-dot" style="background:${r.color}"></div>
        <div>${esc(r.name)}</div>
      </div>
    `).join('');
}

// ─── Playback ───────────────────────────────────────────────────────────────
function togglePlay() {
  if (!replay) return;
  playing = !playing;
  document.getElementById('playBtn').textContent = playing ? '⏸ Pause' : '▶ Play';
  document.getElementById('finishedOverlay').style.display = 'none';

  if (playing) {
    initAudio();
    if (frame >= replay.frames.length - 1) frame = 0;
    lastTime = performance.now();
    accumulator = 0;
    tick();
  } else {
    cancelAnimationFrame(animId);
    pauseSound();
  }
}

function tick() {
  if (!playing || !replay) return;

  const now = performance.now();
  const delta = now - lastTime;
  lastTime = now;
  accumulator += delta;

  const msPerFrame = 1000 / (replay.ticks_per_sec * speed);

  while (accumulator >= msPerFrame) {
    frame++;
    accumulator -= msPerFrame;

    if (frame >= replay.frames.length) {
      frame = replay.frames.length - 1;
      playing = false;
      document.getElementById('playBtn').textContent = '▶ Play';
      break;
    }
  }

  updateCamera(replay, frame);

  if (cameraSystem.mode !== 'full') {
    computeTransform();
    renderBackground();
  }

  render();
  updateSound(replay, frame);
  if (playing) animId = requestAnimationFrame(tick);
}

function setSpeed(s, e) {
  speed = s;
  document.querySelectorAll('.speed-btns button').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
}

document.getElementById('scrubber').addEventListener('input', e => {
  frame = parseInt(e.target.value);
  playing = false;
  document.getElementById('playBtn').textContent = '▶ Play';
  document.getElementById('finishedOverlay').style.display = 'none';
  pauseSound();
  resetPhysicsFx();
  renderBackground();
  render();
});

// ─── Camera keyboard shortcuts ──────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 't' || e.key === 'T') setCameraMode('full');
  if (e.key === 'f' || e.key === 'F') setCameraMode('follow');
  if (e.key === 'o' || e.key === 'O') setCameraMode('onboard');
  if (e.key === 'Escape') setCameraMode('full');
});

// ─── Overlay click: select car from timing tower ────────────────────────────
overlayCanvas.addEventListener('click', e => {
  const rect = overlayCanvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  // Timing tower is on the left, starting at y=60, each row ~30px
  if (x < 200 && replay) {
    const cars = replay.frames[frame];
    if (!cars) return;
    const sorted = [...cars].sort((a, b) => a.position - b.position);
    const rowIdx = Math.floor((y - 60) / 30);
    if (rowIdx >= 0 && rowIdx < sorted.length) {
      selectCar(sorted[rowIdx].name);
    }
  }
});

// ─── Init ───────────────────────────────────────────────────────────────────
resizeAllCanvases();
