// ── Physics Visualization Effects ────────────────────────────────────────────
// Tire marks, brake glow, drafting wake, and visual effects for the race viewer.

const physicsFx = {
  tireMarks: [],   // Array of {x, y, alpha} — persistent marks on track
  maxMarks: 2000,  // Cap to prevent memory issues
};

/**
 * Clear all physics effects state.
 * Called on replay load and when scrubbing.
 */
function resetPhysicsFx() {
  physicsFx.tireMarks = [];
}

/**
 * Add tire marks for cars cornering at speed.
 * @param {Object} replay - full replay object
 * @param {number} frameIdx - current frame index
 * @param {Object} transform - { scale, ox, oy }
 */
function updateTireMarks(replay, frameIdx, transform) {
  const cars = replay.frames[frameIdx];
  if (!cars || !replay.track_curvatures) return;

  const curvatures = replay.track_curvatures;
  const n = curvatures.length;

  for (const car of cars) {
    const seg = car.seg != null ? car.seg % n : 0;
    const curv = curvatures[seg] || 0;

    if (curv > 0.03 && car.speed > 80) {
      physicsFx.tireMarks.push({ x: car.x, y: car.y, alpha: 0.15 });
    }
  }

  // Cap at maxMarks — remove oldest
  if (physicsFx.tireMarks.length > physicsFx.maxMarks) {
    physicsFx.tireMarks.splice(0, physicsFx.tireMarks.length - physicsFx.maxMarks);
  }
}

/**
 * Draw accumulated tire marks on the background canvas.
 * @param {CanvasRenderingContext2D} ctx - background canvas context
 * @param {Object} transform - { scale, ox, oy }
 */
function renderTireMarks(ctx, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;
  const radius = 1.5 * s;

  for (const mark of physicsFx.tireMarks) {
    const sx = mark.x * s + ox;
    const sy = mark.y * s + oy;
    ctx.globalAlpha = mark.alpha;
    ctx.beginPath();
    ctx.arc(sx, sy, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#111';
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

/**
 * Draw a red glow trail behind a braking car.
 * @param {CanvasRenderingContext2D} ctx - car layer context
 * @param {Object} car - current frame car data
 * @param {Object|null} prevCar - same car from previous frame
 * @param {number} screenX - car screen X position
 * @param {number} screenY - car screen Y position
 * @param {number} heading - car heading angle
 * @param {number} scale - world-to-screen scale factor
 */
function renderBrakeGlow(ctx, car, prevCar, screenX, screenY, heading, scale) {
  if (!prevCar) return;

  const speedDrop = prevCar.speed - car.speed;
  if (speedDrop <= 5) return;

  const intensity = Math.min(speedDrop / 30, 1);
  const glowLen = 10 * scale * intensity;
  const glowRadius = 6 * scale * intensity;

  // Position behind the car
  const behindX = screenX - Math.cos(heading) * 8 * scale;
  const behindY = screenY - Math.sin(heading) * 8 * scale;

  ctx.save();
  const grad = ctx.createRadialGradient(
    behindX, behindY, 1,
    behindX, behindY, glowRadius
  );
  grad.addColorStop(0, '#ff00004d');  // red, alpha ~0.3
  grad.addColorStop(0.5, '#ff00001a');
  grad.addColorStop(1, '#ff000000');

  ctx.beginPath();
  ctx.arc(behindX, behindY, glowRadius, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  // Trail line behind the glow
  const trailX = behindX - Math.cos(heading) * glowLen;
  const trailY = behindY - Math.sin(heading) * glowLen;
  ctx.beginPath();
  ctx.moveTo(behindX, behindY);
  ctx.lineTo(trailX, trailY);
  ctx.strokeStyle = '#ff000026';
  ctx.lineWidth = 3 * scale;
  ctx.stroke();
  ctx.restore();
}

/**
 * Draw faint slipstream lines between closely spaced cars.
 * @param {CanvasRenderingContext2D} ctx - car layer context
 * @param {Array} cars - current frame car array
 * @param {Object} replay - full replay object
 * @param {Object} transform - { scale, ox, oy }
 */
function renderDraftingWake(ctx, cars, replay, transform) {
  if (!cars || cars.length < 2) return;

  for (let i = 0; i < cars.length; i++) {
    for (let j = i + 1; j < cars.length; j++) {
      const dx = cars[i].x - cars[j].x;
      const dy = cars[i].y - cars[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 5 || dist > 40) continue;

      const p1 = worldToScreen(cars[i].x, cars[i].y);
      const p2 = worldToScreen(cars[j].x, cars[j].y);

      // Draw 3 thin slipstream lines slightly spread
      ctx.save();
      ctx.globalAlpha = 0.06;
      ctx.strokeStyle = '#ffffff10';
      ctx.lineWidth = 1;

      const perpX = -(p2.y - p1.y) / (dist + 0.001);
      const perpY = (p2.x - p1.x) / (dist + 0.001);

      for (const offset of [-2, 0, 2]) {
        ctx.beginPath();
        ctx.moveTo(p1.x + perpX * offset, p1.y + perpY * offset);
        ctx.lineTo(p2.x + perpX * offset, p2.y + perpY * offset);
        ctx.stroke();
      }
      ctx.restore();
    }
  }
}
