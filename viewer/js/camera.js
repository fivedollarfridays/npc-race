// ── Camera System ─────────────────────────────────────────────────────────────
// Three camera modes: full track, follow cam, onboard cam.
// Smooth lerp transitions between modes.

const cameraSystem = {
  mode: 'full',           // 'full', 'follow', 'onboard'
  targetX: 0,
  targetY: 0,
  targetZoom: 1,
  targetRotation: 0,
  currentX: 0,
  currentY: 0,
  currentZoom: 1,
  currentRotation: 0,
  selectedCar: null,      // car name string
  lerpSpeed: 0.08,        // Per-frame lerp factor
};

/**
 * Switch camera mode. For follow/onboard, auto-selects leader if no car selected.
 */
function setCameraMode(mode) {
  if (mode === 'follow' || mode === 'onboard') {
    if (!cameraSystem.selectedCar) {
      // Auto-select leader if no car selected
      if (typeof replay !== 'undefined' && replay && replay.frames && replay.frames[frame]) {
        const leader = replay.frames[frame].find(c => c.position === 1);
        if (leader) cameraSystem.selectedCar = leader.name;
      }
      if (!cameraSystem.selectedCar) return;
    }
  }
  cameraSystem.mode = mode;
  updateCameraButtons();
}

/**
 * Select a car for follow/onboard cam. Auto-switches to follow if in full mode.
 */
function selectCar(name) {
  cameraSystem.selectedCar = name;
  if (cameraSystem.mode === 'full') {
    setCameraMode('follow');
  }
}

/**
 * Update camera targets based on current mode and frame data.
 * Called each tick before rendering.
 */
function updateCamera(replayData, frameIdx) {
  if (!replayData) return;
  const cars = replayData.frames[frameIdx];
  if (!cars) return;

  if (cameraSystem.mode === 'full') {
    _updateCameraFull();
  } else if (cameraSystem.mode === 'follow') {
    _updateCameraFollow(cars, replayData);
  } else if (cameraSystem.mode === 'onboard') {
    _updateCameraOnboard(cars, replayData);
  }

  _lerpCamera();
}

/**
 * Full track mode: reset to default view.
 */
function _updateCameraFull() {
  cameraSystem.targetZoom = 1;
  cameraSystem.targetRotation = 0;
}

/**
 * Follow cam: track selected car with look-ahead.
 */
function _updateCameraFollow(cars, replayData) {
  const car = cars.find(c => c.name === cameraSystem.selectedCar);
  if (!car) return;

  const heading = _getCarHeading(car, replayData);
  const lookAhead = 30;

  cameraSystem.targetX = car.x + Math.cos(heading) * lookAhead;
  cameraSystem.targetY = car.y + Math.sin(heading) * lookAhead;
  cameraSystem.targetZoom = 3;
  cameraSystem.targetRotation = 0;
}

/**
 * Onboard cam: tight zoom with rotation so car faces up.
 */
function _updateCameraOnboard(cars, replayData) {
  const car = cars.find(c => c.name === cameraSystem.selectedCar);
  if (!car) return;

  const heading = _getCarHeading(car, replayData);
  const lookAhead = 20;

  cameraSystem.targetX = car.x + Math.cos(heading) * lookAhead;
  cameraSystem.targetY = car.y + Math.sin(heading) * lookAhead;
  cameraSystem.targetZoom = 6;
  cameraSystem.targetRotation = -heading + Math.PI / 2;
}

/**
 * Get heading angle for a car from track headings data.
 */
function _getCarHeading(car, replayData) {
  if (replayData.track_headings && car.seg !== undefined) {
    return replayData.track_headings[car.seg] || 0;
  }
  return 0;
}

/**
 * Lerp current values toward targets for smooth transitions.
 */
function _lerpCamera() {
  const s = cameraSystem.lerpSpeed;
  cameraSystem.currentX += (cameraSystem.targetX - cameraSystem.currentX) * s;
  cameraSystem.currentY += (cameraSystem.targetY - cameraSystem.currentY) * s;
  cameraSystem.currentZoom += (cameraSystem.targetZoom - cameraSystem.currentZoom) * s;
  cameraSystem.currentRotation +=
    (cameraSystem.targetRotation - cameraSystem.currentRotation) * s;
}

/**
 * Update active state on camera mode buttons in the UI.
 */
function updateCameraButtons() {
  document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('cam-' + cameraSystem.mode);
  if (btn) btn.classList.add('active');
}
