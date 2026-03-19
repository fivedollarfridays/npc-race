// Timing tower — Sprint 8 T8.3
// State
let _selectedCar = null;
let _prevGaps = {};

function initTimingTower(replay) {
  const container = document.getElementById('towerRows');
  if (!container) return;
  container.innerHTML = '';
  _prevGaps = {};

  const cars = replay.frames[0];
  cars.forEach(car => {
    const row = document.createElement('div');
    row.className = 'tower-row';
    row.dataset.carName = car.name;
    row.innerHTML = `
      <span class="tower-pos">--</span>
      <span class="tower-color" style="background:${car.color}"></span>
      <span class="tower-name">${car.name.substring(0, 3).toUpperCase()}</span>
      <span class="tower-gap">---</span>
      <span class="tower-compound">●</span>
      <span class="tower-tire-age">--</span>
      <span class="tower-wear-bar"><span class="wear-fill"></span></span>
    `;
    row.addEventListener('click', () => selectCar(car.name));
    container.appendChild(row);
  });

  if (cars.length > 0) {
    selectCar(cars[0].name);
  }
}

function updateTimingTower(frameCars, selectedCar) {
  if (!frameCars || frameCars.length === 0) return;

  const sorted = [...frameCars].sort((a, b) => a.position - b.position);

  let fastestLapCar = null;
  let fastestLapTime = Infinity;
  sorted.forEach(car => {
    if (car.best_lap_s && car.best_lap_s < fastestLapTime) {
      fastestLapTime = car.best_lap_s;
      fastestLapCar = car.name;
    }
  });

  const rows = document.querySelectorAll('.tower-row');
  sorted.forEach((car, idx) => {
    const row = rows[idx] || document.querySelector(`[data-car-name="${car.name}"]`);
    if (!row) return;

    // Position
    const posEl = row.querySelector('.tower-pos');
    posEl.textContent = car.name === fastestLapCar
      ? `P${car.position} \u25CF`
      : `P${car.position}`;
    if (car.name === fastestLapCar) posEl.classList.add('fastest-lap');
    else posEl.classList.remove('fastest-lap');

    // Gap
    const gapEl = row.querySelector('.tower-gap');
    if (car.position === 1) {
      gapEl.textContent = 'LEADER';
      gapEl.className = 'tower-gap';
    } else {
      const gap = car.gap_ahead_s || 0;
      gapEl.textContent = `+${gap.toFixed(3)}s`;
      const prevGap = _prevGaps[car.name] || gap;
      if (gap < prevGap - 0.01) {
        gapEl.className = 'tower-gap gaining';
      } else if (gap > prevGap + 0.01) {
        gapEl.className = 'tower-gap losing';
      } else {
        gapEl.className = 'tower-gap';
      }
      _prevGaps[car.name] = gap;
    }

    // Tire compound dot
    const compEl = row.querySelector('.tower-compound');
    const comp = car.tire_compound || 'medium';
    compEl.className = `tower-compound compound-${comp}`;
    compEl.textContent = '\u25CF';

    // Tire age
    row.querySelector('.tower-tire-age').textContent =
      `${car.tire_age_laps || 0}L`;

    // Wear bar
    const wear = car.tire_wear || 0;
    const fill = row.querySelector('.wear-fill');
    if (fill) {
      fill.style.width = `${(1 - wear) * 100}%`;
      fill.className = 'wear-fill'
        + (wear > 0.75 ? ' wear-critical' : wear > 0.5 ? ' wear-warning' : '');
    }

    // Selected highlight
    row.classList.toggle('selected', car.name === selectedCar);

    // Pit status
    row.classList.toggle('in-pit', car.pit_status !== 'racing');

    // Finished
    row.classList.toggle('finished', car.finished === true);
    if (car.finished) {
      gapEl.textContent = 'FIN';
    }

    // Reorder DOM to match position
    row.style.order = car.position;
  });

  // Update fastest lap footer
  const footer = document.getElementById('fastestLapInfo');
  if (footer && fastestLapCar) {
    const m = Math.floor(fastestLapTime / 60);
    const s = fastestLapTime % 60;
    footer.textContent =
      `Best: ${m}:${s.toFixed(3).padStart(6, '0')} (${fastestLapCar.substring(0, 3).toUpperCase()})`;
    footer.style.color = 'var(--accent-purple)';
  }
}

function selectCar(carName) {
  _selectedCar = carName;
  document.querySelectorAll('.tower-row').forEach(row => {
    row.classList.toggle('selected', row.dataset.carName === carName);
  });
  document.dispatchEvent(
    new CustomEvent('car-selected', { detail: { name: carName } })
  );
}
