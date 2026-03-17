// Data enrichment — derive missing fields for backward compat
function enrichReplayData(replay) {
  const track = replay.track;
  const n = track.length;

  // Compute headings if missing
  if (!replay.track_headings) {
    replay.track_headings = [];
    for (let i = 0; i < n; i++) {
      const next = track[(i + 1) % n];
      const dx = next.x - track[i].x;
      const dy = next.y - track[i].y;
      replay.track_headings.push(Math.atan2(dy, dx));
    }
  }

  // Compute curvatures if missing
  if (!replay.track_curvatures) {
    replay.track_curvatures = [];
    for (let i = 0; i < n; i++) {
      const p0 = track[(i - 1 + n) % n];
      const p1 = track[i];
      const p2 = track[(i + 1) % n];
      const dx1 = p1.x - p0.x, dy1 = p1.y - p0.y;
      const dx2 = p2.x - p1.x, dy2 = p2.y - p1.y;
      const cross = Math.abs(dx1 * dy2 - dy1 * dx2);
      const d1 = Math.sqrt(dx1 * dx1 + dy1 * dy1) + 0.001;
      const d2 = Math.sqrt(dx2 * dx2 + dy2 * dy2) + 0.001;
      replay.track_curvatures.push(cross / (d1 * d2));
    }
  }

  // Compute distances array (needed for seg lookup)
  if (!replay._distances) {
    replay._distances = [0];
    for (let i = 1; i < n; i++) {
      const dx = track[i].x - track[i - 1].x;
      const dy = track[i].y - track[i - 1].y;
      replay._distances.push(replay._distances[i - 1] + Math.sqrt(dx * dx + dy * dy));
    }
    // Total length including closing segment
    const dx = track[0].x - track[n - 1].x;
    const dy = track[0].y - track[n - 1].y;
    replay._trackLength = replay._distances[n - 1] + Math.sqrt(dx * dx + dy * dy);
  }

  // Compute track normals (needed for edge lines, kerbs)
  if (!replay._normals) {
    replay._normals = [];
    for (let i = 0; i < n; i++) {
      const next = track[(i + 1) % n];
      const dx = next.x - track[i].x;
      const dy = next.y - track[i].y;
      const len = Math.sqrt(dx * dx + dy * dy) + 0.001;
      replay._normals.push({ x: -dy / len, y: dx / len });
    }
  }
}
