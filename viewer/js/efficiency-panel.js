/**
 * Live efficiency HUD — shows per-part efficiency bars during race.
 * Sprint 46 T46.4 + T46.5 (ghost column)
 */

let effPanel = null;

function initEfficiencyPanel(replay) {
    const container = document.getElementById('efficiency-panel');
    if (!container) return;

    const parts = ['gearbox', 'cooling', 'product'];
    const labels = {'gearbox': 'Gearbox', 'cooling': 'Cooling', 'product': 'Combined'};

    let html = '<div class="eff-header">EFFICIENCY</div>';

    // Header row with You / Ghost labels
    html += '<div class="eff-row">';
    html += '<span class="eff-label"></span>';
    html += '<span style="flex:1"></span>';
    html += '<span style="width:40px;text-align:right;color:#7c3aed">You</span>';
    html += '<span style="width:40px;text-align:right;color:#666">Ghost</span>';
    html += '</div>';

    for (const part of parts) {
        html += `
            <div class="eff-row" id="eff-${part}">
                <span class="eff-label">${labels[part]}</span>
                <div class="eff-bar-bg">
                    <div class="eff-bar-fill" id="eff-bar-${part}"></div>
                </div>
                <span class="eff-value" id="eff-val-${part}">&mdash;</span>
                <span class="eff-ghost" id="eff-ghost-${part}" style="color:#666;width:40px;text-align:right">&mdash;</span>
            </div>
        `;
    }

    // Ghost delta display
    html += '<div class="eff-row" style="margin-top:6px;border-top:1px solid #30363d;padding-top:6px">';
    html += '<span class="eff-label">Gap</span>';
    html += '<span id="ghost-delta" style="flex:1;text-align:right;font-weight:bold">&mdash;</span>';
    html += '</div>';

    container.innerHTML = html;
    effPanel = container;
}

function updateEfficiencyPanel(carData, allCars) {
    if (!effPanel) return;

    const mappings = {
        'gearbox': 'gearbox_efficiency',
        'cooling': 'cooling_efficiency',
        'product': 'efficiency_product',
    };

    // Find ghost car in current frame
    const ghostCar = allCars ? allCars.find(c => isGhostCar(c)) : null;

    for (const [key, field] of Object.entries(mappings)) {
        const val = carData[field];
        if (val === undefined || val === null) continue;

        const bar = document.getElementById(`eff-bar-${key}`);
        const label = document.getElementById(`eff-val-${key}`);
        if (!bar || !label) continue;

        const pct = Math.round(val * 100);
        bar.style.width = `${pct}%`;
        label.textContent = val.toFixed(2);

        // Color: green >= 0.95, yellow 0.85-0.95, red < 0.85
        if (val >= 0.95) {
            bar.style.backgroundColor = '#22c55e';
        } else if (val >= 0.85) {
            bar.style.backgroundColor = '#eab308';
        } else {
            bar.style.backgroundColor = '#ef4444';
        }

        // Ghost comparison column
        const ghostLabel = document.getElementById(`eff-ghost-${key}`);
        if (ghostLabel && ghostCar) {
            const gVal = ghostCar[field] || 0;
            ghostLabel.textContent = gVal.toFixed(2);
            ghostLabel.style.color = gVal < val ? '#ef4444' : '#22c55e';
        }
    }

    // Update ghost delta (gap display)
    if (ghostCar) {
        updateGhostDelta(carData, ghostCar);
    }
}

function updateGhostDelta(playerCar, ghostCar) {
    const delta = document.getElementById('ghost-delta');
    if (!delta || !ghostCar) return;

    const gap = playerCar.gap_ahead_s || 0;
    if (ghostCar.position < playerCar.position) {
        delta.textContent = `+${gap.toFixed(1)}s`;
        delta.style.color = '#ef4444';
    } else {
        delta.textContent = `-${gap.toFixed(1)}s`;
        delta.style.color = '#22c55e';
    }
}
