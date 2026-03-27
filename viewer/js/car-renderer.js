// ─── Car Renderer ───────────────────────────────────────────────────────────
// Top-down realistic race car rendering with wheels, effects, and labels.

/**
 * Darken a hex color by a given fraction (0–1).
 */
function darkenColor(hex, amount) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const f = 1 - amount;
  return (
    '#' +
    Math.round(r * f).toString(16).padStart(2, '0') +
    Math.round(g * f).toString(16).padStart(2, '0') +
    Math.round(b * f).toString(16).padStart(2, '0')
  );
}

/**
 * Clamp a number between min and max.
 */
function clamp(val, lo, hi) {
  return Math.max(lo, Math.min(hi, val));
}

/**
 * Compute the steering angle based on heading look-ahead.
 * Returns a clamped angle delta between current and future track heading.
 */
function computeSteerAngle(replay, seg) {
  if (!replay.track_headings) return 0;
  const n = replay.track_headings.length;
  const current = replay.track_headings[seg % n];
  const ahead = replay.track_headings[(seg + 5) % n];
  let delta = ahead - current;
  // Normalize to [-PI, PI]
  while (delta > Math.PI) delta -= 2 * Math.PI;
  while (delta < -Math.PI) delta += 2 * Math.PI;
  return clamp(delta, -0.3, 0.3);
}

/**
 * Draw a single wheel (dark rectangle).
 * @param {CanvasRenderingContext2D} ctx
 * @param {number} x - center x in local car coords
 * @param {number} y - center y in local car coords
 * @param {number} wLen - wheel length (scaled)
 * @param {number} wWid - wheel width (scaled)
 * @param {number} angle - additional rotation (steering)
 */
function drawWheel(ctx, x, y, wLen, wWid, angle) {
  ctx.save();
  ctx.translate(x, y);
  if (angle) ctx.rotate(angle);
  ctx.fillStyle = '#111';
  ctx.fillRect(-wLen / 2, -wWid / 2, wLen, wWid);
  ctx.restore();
}

/**
 * Draw a shadow ellipse beneath the car.
 */
function drawShadow(ctx, bodyLen, bodyWid) {
  ctx.save();
  ctx.translate(2, 2);
  ctx.beginPath();
  ctx.ellipse(0, 0, bodyLen / 2 + 1, bodyWid / 2 + 1, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#00000044';
  ctx.fill();
  ctx.restore();
}

/**
 * Draw the main car body as a tapered shape with nose cone.
 */
function drawBody(ctx, bodyLen, bodyWid, color) {
  const halfL = bodyLen / 2;
  const halfW = bodyWid / 2;
  const noseW = halfW * 0.6;

  ctx.beginPath();
  // Start at rear-left, go clockwise
  ctx.moveTo(-halfL, -halfW);
  // Left side to front taper point
  ctx.lineTo(halfL * 0.4, -halfW);
  // Nose cone left
  ctx.lineTo(halfL, -noseW);
  // Nose tip (rounded)
  ctx.quadraticCurveTo(halfL + 2, 0, halfL, noseW);
  // Nose cone right
  ctx.lineTo(halfL * 0.4, halfW);
  // Right side to rear
  ctx.lineTo(-halfL, halfW);
  // Rear
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

/**
 * Draw a cockpit area (darker oval in front-center).
 */
function drawCockpit(ctx, bodyLen, bodyWid, color) {
  const cockpitX = bodyLen * 0.1;
  const cockpitW = bodyLen * 0.18;
  const cockpitH = bodyWid * 0.3;
  ctx.beginPath();
  ctx.ellipse(cockpitX, 0, cockpitW, cockpitH, 0, 0, Math.PI * 2);
  ctx.fillStyle = darkenColor(color, 0.3);
  ctx.fill();
}

/**
 * Draw the rear wing (thin dark bar at the back, slightly wider than body).
 */
function drawRearWing(ctx, bodyLen, bodyWid) {
  const wingX = -bodyLen / 2 - 1;
  const wingW = bodyWid * 0.6;
  const wingH = 2;
  ctx.fillStyle = '#222';
  ctx.fillRect(wingX - wingH / 2, -wingW, wingH, wingW * 2);
}

/**
 * Draw four wheels at the corners of the car body.
 */
function drawWheels(ctx, bodyLen, bodyWid, scale, steerAngle) {
  const wLen = 3 * scale;
  const wWid = 1.5 * scale;
  const halfL = bodyLen / 2;
  const halfW = bodyWid / 2;

  // Front wheels (with steering)
  drawWheel(ctx, halfL * 0.55, -halfW + wWid * 0.3, wLen, wWid, steerAngle);
  drawWheel(ctx, halfL * 0.55, halfW - wWid * 0.3, wLen, wWid, steerAngle);

  // Rear wheels (no steering)
  drawWheel(ctx, -halfL * 0.6, -halfW + wWid * 0.3, wLen, wWid, 0);
  drawWheel(ctx, -halfL * 0.6, halfW - wWid * 0.3, wLen, wWid, 0);
}

/**
 * Draw brake lights (two small red circles at rear).
 * Only glow when braking (speed drop > 2 km/h).
 */
function drawBrakeLights(ctx, bodyLen, bodyWid, isBraking) {
  if (!isBraking) return;

  const rearX = -bodyLen / 2 + 1;
  const spread = bodyWid * 0.3;
  const radius = 2;

  for (const offsetY of [-spread, spread]) {
    const grad = ctx.createRadialGradient(
      rearX, offsetY, 0,
      rearX, offsetY, radius * 3
    );
    grad.addColorStop(0, '#ff0000');
    grad.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(rearX, offsetY, radius * 3, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(rearX, offsetY, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#ff0000';
    ctx.fill();
  }
}

/**
 * Draw subtle boost exhaust glow behind the car.
 */
function drawBoostGlow(ctx, bodyLen, color) {
  const rearX = -bodyLen / 2;
  const glowRadius = bodyLen * 0.6;
  const grad = ctx.createRadialGradient(
    rearX, 0, 2,
    rearX - glowRadius * 0.3, 0, glowRadius
  );
  grad.addColorStop(0, color + '88');
  grad.addColorStop(0.3, '#ff880044');
  grad.addColorStop(1, '#ff880000');
  ctx.beginPath();
  ctx.arc(rearX - glowRadius * 0.15, 0, glowRadius, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();
}

/**
 * Draw the position number on the car body.
 */
function drawPositionNumber(ctx, position) {
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 8px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(position, 0, 0);
}

/**
 * Render a single top-down race car.
 *
 * @param {CanvasRenderingContext2D} ctx - car layer context
 * @param {Object} car - current frame car data (x, y, name, color, speed, position, boost, seg, ...)
 * @param {Object|null} prevCar - same car from previous frame (for braking detection)
 * @param {Object} replay - full replay object (track_headings, track, etc.)
 * @param {Object} transform - { scale, ox, oy }
 */
function renderCar(ctx, car, prevCar, replay, transform) {
  const pos = worldToScreen(car.x, car.y);
  const sx = pos.x;
  const sy = pos.y;
  const s = transform.scale;

  // Car dimensions in screen units
  const bodyLen = 14 * s;
  const bodyWid = 6 * s;

  // Heading from track_headings
  const heading = (replay.track_headings && car.seg != null)
    ? replay.track_headings[car.seg % replay.track_headings.length]
    : 0;

  // Steering angle for front wheels
  const steerAngle = computeSteerAngle(replay, car.seg || 0);

  // Braking detection
  const isBraking = prevCar != null && (car.speed < prevCar.speed - 2);

  // Ghost cars render translucent
  if (isGhostCar(car)) {
    ctx.globalAlpha = 0.5;
  }

  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(heading);

  // 1. Shadow
  drawShadow(ctx, bodyLen, bodyWid);

  // 2. Boost glow (behind car, drawn before body)
  if (car.boost) {
    drawBoostGlow(ctx, bodyLen, car.color);
  }

  // 3. Car body
  drawBody(ctx, bodyLen, bodyWid, car.color);

  // 4. Cockpit
  drawCockpit(ctx, bodyLen, bodyWid, car.color);

  // 5. Rear wing
  drawRearWing(ctx, bodyLen, bodyWid);

  // 6. Wheels
  drawWheels(ctx, bodyLen, bodyWid, s, steerAngle);

  // 7. Brake lights
  drawBrakeLights(ctx, bodyLen, bodyWid, isBraking);

  // 8. Position number
  drawPositionNumber(ctx, car.position);

  ctx.restore();

  // 9. Name label — 3-letter abbreviation in car color (Sprint 15)
  ctx.fillStyle = car.color || '#ddd';
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(getCarAbbrev(car.name), sx, sy - bodyWid / 2 - 4);

  // Reset alpha after ghost rendering
  if (isGhostCar(car)) {
    ctx.globalAlpha = 1.0;
  }
}

function getCarAbbrev(name) {
  return (name || '???').substring(0, 3).toUpperCase();
}

/**
 * Detect whether a car object represents a ghost car.
 */
function isGhostCar(car) {
  return car.name === 'Ghost' || car.name === 'Tortoise' || car.color === '#555555';
}
