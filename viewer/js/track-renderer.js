// ─── Track Renderer ─────────────────────────────────────────────────────────
// Renders the track with realistic visuals on the background canvas.
// Called from renderBackground() in main.js.

function _drawTrackPath(ctx, track, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;
  ctx.moveTo(track[0].x * s + ox, track[0].y * s + oy);
  for (let i = 1; i < track.length; i++) {
    ctx.lineTo(track[i].x * s + ox, track[i].y * s + oy);
  }
  ctx.closePath();
}

function _drawGrass(ctx, transform) {
  // Green grass background
  ctx.fillStyle = '#1a3a1a';
  ctx.fillRect(0, 0, transform.w, transform.h);

  // Subtle darker patches for texture variation
  ctx.fillStyle = '#15321a';
  const patchSize = 40;
  for (let y = 0; y < transform.h; y += patchSize) {
    for (let x = 0; x < transform.w; x += patchSize) {
      if ((x * 7 + y * 13) % 5 === 0) {
        ctx.fillRect(x, y, patchSize * 0.6, patchSize * 0.6);
      }
    }
  }
}

function _drawRunoff(ctx, track, trackWidth, transform) {
  // Run-off area: wider stroke in gravel gray
  ctx.beginPath();
  _drawTrackPath(ctx, track, transform);
  ctx.strokeStyle = '#3a3a3a';
  ctx.lineWidth = trackWidth * transform.scale * 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();
}

function _drawAsphalt(ctx, track, trackWidth, transform) {
  // Asphalt surface
  ctx.beginPath();
  _drawTrackPath(ctx, track, transform);
  ctx.strokeStyle = '#252530';
  ctx.lineWidth = trackWidth * transform.scale;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Noise texture overlay via offscreen pattern
  const texCanvas = document.createElement('canvas');
  texCanvas.width = 4;
  texCanvas.height = 4;
  const texCtx = texCanvas.getContext('2d');
  const imgData = texCtx.createImageData(4, 4);
  for (let i = 0; i < imgData.data.length; i += 4) {
    const v = 30 + ((i * 7) % 15);
    imgData.data[i] = v;
    imgData.data[i + 1] = v;
    imgData.data[i + 2] = v + 5;
    imgData.data[i + 3] = 25;
  }
  texCtx.putImageData(imgData, 0, 0);

  const pattern = ctx.createPattern(texCanvas, 'repeat');
  ctx.beginPath();
  _drawTrackPath(ctx, track, transform);
  ctx.strokeStyle = pattern;
  ctx.lineWidth = trackWidth * transform.scale;
  ctx.stroke();
}

function _drawEdgeLines(ctx, track, normals, halfWidth, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;

  // Left edge
  ctx.beginPath();
  for (let i = 0; i < track.length; i++) {
    const ex = (track[i].x + normals[i].x * halfWidth) * s + ox;
    const ey = (track[i].y + normals[i].y * halfWidth) * s + oy;
    if (i === 0) ctx.moveTo(ex, ey);
    else ctx.lineTo(ex, ey);
  }
  ctx.closePath();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Right edge
  ctx.beginPath();
  for (let i = 0; i < track.length; i++) {
    const ex = (track[i].x - normals[i].x * halfWidth) * s + ox;
    const ey = (track[i].y - normals[i].y * halfWidth) * s + oy;
    if (i === 0) ctx.moveTo(ex, ey);
    else ctx.lineTo(ex, ey);
  }
  ctx.closePath();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.5;
  ctx.stroke();
}

function _drawKerbs(ctx, track, normals, curvatures, halfWidth, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;
  const kerbThreshold = 0.04;
  const kerbWidth = 4;

  for (let i = 0; i < track.length; i++) {
    if (curvatures[i] < kerbThreshold) continue;

    // Determine inside direction from cross product sign
    const prev = (i - 1 + track.length) % track.length;
    const next = (i + 1) % track.length;
    const dx1 = track[i].x - track[prev].x;
    const dy1 = track[i].y - track[prev].y;
    const dx2 = track[next].x - track[i].x;
    const dy2 = track[next].y - track[i].y;
    const cross = dx1 * dy2 - dy1 * dx2;
    const sign = cross > 0 ? 1 : -1;

    // Inside edge position
    const ex = (track[i].x + normals[i].x * halfWidth * sign) * s + ox;
    const ey = (track[i].y + normals[i].y * halfWidth * sign) * s + oy;

    // Alternating red (#cc0000) / white kerb blocks
    ctx.fillStyle = (i % 2 === 0) ? '#cc0000' : '#ffffff';
    ctx.fillRect(ex - kerbWidth / 2, ey - kerbWidth / 2, kerbWidth, kerbWidth);
  }
}

function _drawRacingLine(ctx, track, curvatures, normals, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;

  ctx.beginPath();
  ctx.setLineDash([6, 10]);
  ctx.strokeStyle = '#333340';
  ctx.lineWidth = 1;

  for (let i = 0; i < track.length; i++) {
    // Bias toward inside at corners
    let biasX = 0;
    let biasY = 0;
    if (curvatures[i] > 0.02) {
      const prev = (i - 1 + track.length) % track.length;
      const next = (i + 1) % track.length;
      const dx1 = track[i].x - track[prev].x;
      const dy1 = track[i].y - track[prev].y;
      const dx2 = track[next].x - track[i].x;
      const dy2 = track[next].y - track[i].y;
      const cross = dx1 * dy2 - dy1 * dx2;
      const sign = cross > 0 ? 1 : -1;
      const bias = Math.min(curvatures[i] * 5, 0.3);
      biasX = normals[i].x * bias * sign * 10;
      biasY = normals[i].y * bias * sign * 10;
    }

    const px = (track[i].x + biasX) * s + ox;
    const py = (track[i].y + biasY) * s + oy;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }

  ctx.closePath();
  ctx.stroke();
  ctx.setLineDash([]);
}

function _drawStartFinish(ctx, track, normals, halfWidth, transform) {
  const s = transform.scale;
  const ox = transform.ox;
  const oy = transform.oy;

  // Heading direction at track[0]
  const next = track[1];
  const dx = next.x - track[0].x;
  const dy = next.y - track[0].y;
  const len = Math.sqrt(dx * dx + dy * dy) + 0.001;
  const hdx = dx / len;
  const hdy = dy / len;

  const nx = normals[0].x;
  const ny = normals[0].y;
  const gridCount = 6;
  const gridSize = (halfWidth * 2) / gridCount;
  const lineDepth = gridSize;

  // Checkered pattern across track width
  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < gridCount; col++) {
      const isBlack = (row + col) % 2 === 0;
      ctx.fillStyle = isBlack ? '#111111' : '#ffffff';

      const offsetAlong = (row - 0.5) * lineDepth;
      const offsetAcross = (col - gridCount / 2 + 0.5) * gridSize;

      const cx = track[0].x + hdx * offsetAlong + nx * offsetAcross;
      const cy = track[0].y + hdy * offsetAlong + ny * offsetAcross;

      const sx = cx * s + ox;
      const sy = cy * s + oy;
      const sz = gridSize * s;

      ctx.fillRect(sx - sz / 2, sy - sz / 2, sz, sz);
    }
  }
}

function renderTrack(ctx, replay, transform) {
  if (!replay || !replay.track) return;

  const track = replay.track;
  const trackWidth = replay.track_width || 12;
  const halfWidth = trackWidth / 2;
  const normals = replay._normals || [];
  const curvatures = replay.track_curvatures || [];

  // Layer 1: grass
  _drawGrass(ctx, transform);

  // Layer 2: run-off areas
  _drawRunoff(ctx, track, trackWidth, transform);

  // Layer 3: asphalt surface with texture
  _drawAsphalt(ctx, track, trackWidth, transform);

  // Layer 4: white edge lines
  if (normals.length === track.length) {
    _drawEdgeLines(ctx, track, normals, halfWidth, transform);
  }

  // Layer 5: red/white kerbs at corners
  if (normals.length === track.length && curvatures.length === track.length) {
    _drawKerbs(ctx, track, normals, curvatures, halfWidth, transform);
  }

  // Layer 6: racing line
  if (curvatures.length === track.length && normals.length === track.length) {
    _drawRacingLine(ctx, track, curvatures, normals, transform);
  }

  // Layer 7: start/finish checkered line
  if (normals.length > 0) {
    _drawStartFinish(ctx, track, normals, halfWidth, transform);
  }
}
