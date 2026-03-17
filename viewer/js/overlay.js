// ─── Broadcast Overlay ──────────────────────────────────────────────────────
// F1 TV-style overlay rendered on the overlay canvas layer.

const overlayState = {
  overtakeQueue: [],      // {text, startTime, duration}
  selectedCar: null,      // name of selected car for follow cam
  lapTimes: {},           // {carName: [frameCounts per lap]}
  fastestLap: null,       // {carName, frames}
  lastPositions: {},      // {carName: position} from previous frame
  lastLaps: {},           // {carName: lap} for detecting lap boundaries
  lapStartFrames: {},     // {carName: frameIndex} when current lap started
};

// ─── Timing Tower ───────────────────────────────────────────────────────────
function renderTimingTower(ctx, cars, replay, w, h) {
  const sorted = [...cars].sort((a, b) => a.position - b.position);
  const startY = 60;
  const rowH = 30;
  const x = 16;
  const colW = 200;

  // Background panel
  const panelH = sorted.length * rowH + 12;
  ctx.save();
  ctx.beginPath();
  _roundRect(ctx, x - 8, startY - 6, colW, panelH, 6);
  ctx.fillStyle = 'rgba(10, 10, 15, 0.82)';
  ctx.fill();
  ctx.restore();

  for (let i = 0; i < sorted.length; i++) {
    const car = sorted[i];
    const y = startY + i * rowH;

    // P1 gold accent bar
    if (car.position === 1) {
      ctx.fillStyle = 'rgba(255, 215, 0, 0.15)';
      ctx.fillRect(x - 8, y - 2, colW, rowH - 2);
    }

    // Position number
    ctx.font = 'bold 14px JetBrains Mono';
    ctx.fillStyle = car.position === 1 ? '#ffd700' : '#ccc';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(car.position, x + 20, y + 12);

    // Color bar
    ctx.fillStyle = car.color;
    ctx.fillRect(x + 26, y + 3, 4, 20);

    // 3-char abbreviation
    const abbr = car.name.substring(0, 3).toUpperCase();
    ctx.font = '600 13px Outfit';
    ctx.fillStyle = '#e0e0e0';
    ctx.textAlign = 'left';
    ctx.fillText(abbr, x + 36, y + 12);

    // Speed
    ctx.font = '12px JetBrains Mono';
    ctx.fillStyle = '#888';
    ctx.textAlign = 'right';
    ctx.fillText(`${Math.round(car.speed)} km/h`, x + colW - 16, y + 12);

    // Fastest lap purple dot
    if (overlayState.fastestLap && overlayState.fastestLap.carName === car.name) {
      ctx.beginPath();
      ctx.arc(x + colW - 8, y + 4, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#9900ff';
      ctx.fill();
    }
  }
}

// ─── Lap Counter ────────────────────────────────────────────────────────────
function renderLapCounter(ctx, replay, frame, w, h) {
  const cars = replay.frames[frame];
  if (!cars || cars.length === 0) return;

  const leader = cars.reduce((a, b) => a.position < b.position ? a : b);
  const currentLap = Math.min(leader.lap + 1, replay.laps);
  const text = `LAP ${currentLap} / ${replay.laps}`;

  const cx = w / 2;
  const y = 24;

  // Background bar
  ctx.save();
  const metrics = ctx.measureText(text);
  ctx.font = '600 16px Outfit';
  const tw = ctx.measureText(text).width;
  ctx.beginPath();
  _roundRect(ctx, cx - tw / 2 - 16, y - 14, tw + 32, 30, 6);
  ctx.fillStyle = 'rgba(10, 10, 15, 0.82)';
  ctx.fill();

  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, cx, y);
  ctx.restore();
}

// ─── Race Status Badge ──────────────────────────────────────────────────────
function renderRaceStatus(ctx, replay, frame, w, h) {
  const cars = replay.frames[frame];
  if (!cars || cars.length === 0) return;

  const leader = cars.reduce((a, b) => a.position < b.position ? a : b);

  let label, bgColor;
  if (leader.finished) {
    label = 'CHEQUERED FLAG';
    bgColor = '#666';
  } else if (leader.lap >= replay.laps - 1) {
    label = 'FINAL LAP';
    bgColor = '#ccaa00';
  } else {
    label = 'RACE';
    bgColor = '#44cc44';
  }

  const cx = w / 2;
  const y = 56;

  ctx.save();
  ctx.font = 'bold 11px Outfit';
  const tw = ctx.measureText(label).width;
  ctx.beginPath();
  _roundRect(ctx, cx - tw / 2 - 10, y - 10, tw + 20, 22, 4);
  ctx.fillStyle = bgColor;
  ctx.fill();

  ctx.fillStyle = '#000';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, cx, y);
  ctx.restore();
}

// ─── Speed Readout ──────────────────────────────────────────────────────────
function renderSpeedReadout(ctx, cars, w, h) {
  if (!cars || cars.length === 0) return;

  const leader = cars.reduce((a, b) => a.position < b.position ? a : b);
  const text = `${Math.round(leader.speed)} km/h`;

  const cx = w / 2 + 120;
  const y = 24;

  ctx.save();
  ctx.font = '14px JetBrains Mono';
  ctx.fillStyle = '#aaa';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, cx, y);
  ctx.restore();
}

// ─── Overtake Notifications ─────────────────────────────────────────────────
function renderOvertakeNotification(ctx, cars, prevCars, w, h, currentTime) {
  if (prevCars) {
    for (const car of cars) {
      const prev = prevCars.find(c => c.name === car.name);
      if (!prev) continue;
      if (car.position < prev.position) {
        // Car gained a position -- find who was displaced
        const displaced = cars.find(c => c.position === prev.position && c.name !== car.name);
        const displacedName = displaced ? displaced.name : '???';
        const text = `OVERTAKE \u2014 ${car.name} passes ${displacedName} for P${car.position}`;
        overlayState.overtakeQueue.push({
          text,
          startTime: currentTime,
          duration: 2000,
        });
      }
    }
  }

  // Draw active notifications
  const active = overlayState.overtakeQueue.filter(
    n => currentTime - n.startTime < n.duration
  );
  // Keep only recent (max 3)
  while (overlayState.overtakeQueue.length > 10) {
    overlayState.overtakeQueue.shift();
  }

  for (let i = 0; i < Math.min(active.length, 3); i++) {
    const notif = active[i];
    const elapsed = currentTime - notif.startTime;
    const alpha = Math.max(0, 1 - elapsed / notif.duration);

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.font = 'bold 14px Outfit';
    const tw = ctx.measureText(notif.text).width;
    const nx = w / 2;
    const ny = h - 60 - i * 36;

    ctx.beginPath();
    _roundRect(ctx, nx - tw / 2 - 16, ny - 14, tw + 32, 30, 6);
    ctx.fillStyle = 'rgba(10, 10, 15, 0.85)';
    ctx.fill();

    ctx.fillStyle = '#ff6600';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(notif.text, nx, ny);
    ctx.restore();
  }
}

// ─── Fastest Lap Tracking ───────────────────────────────────────────────────
function renderFastestLap(ctx, replay, frame, cars) {
  if (!cars) return;

  for (const car of cars) {
    const prevLap = overlayState.lastLaps[car.name];
    if (prevLap !== undefined && car.lap > prevLap) {
      // Lap boundary crossed
      const startFrame = overlayState.lapStartFrames[car.name];
      if (startFrame !== undefined) {
        const lapFrames = frame - startFrame;
        if (!overlayState.lapTimes[car.name]) {
          overlayState.lapTimes[car.name] = [];
        }
        overlayState.lapTimes[car.name].push(lapFrames);

        if (!overlayState.fastestLap || lapFrames < overlayState.fastestLap.frames) {
          overlayState.fastestLap = { carName: car.name, frames: lapFrames };
        }
      }
      overlayState.lapStartFrames[car.name] = frame;
    }
    if (overlayState.lastLaps[car.name] === undefined) {
      overlayState.lapStartFrames[car.name] = 0;
    }
    overlayState.lastLaps[car.name] = car.lap;
  }
}

// ─── Main Entry Point ───────────────────────────────────────────────────────
function renderBroadcastOverlay(ctx, replay, frame, w, h) {
  const cars = replay.frames[frame];
  if (!cars) return;
  const prevCars = frame > 0 ? replay.frames[frame - 1] : null;

  renderFastestLap(ctx, replay, frame, cars);
  renderTimingTower(ctx, cars, replay, w, h);
  renderLapCounter(ctx, replay, frame, w, h);
  renderRaceStatus(ctx, replay, frame, w, h);
  renderSpeedReadout(ctx, cars, w, h);
  renderOvertakeNotification(ctx, cars, prevCars, w, h, performance.now());
}

// ─── Utility ────────────────────────────────────────────────────────────────
function _roundRect(ctx, x, y, w, h, r) {
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
