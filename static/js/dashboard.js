// Dashboard Controller
let speedChartInstance = null;
let fuelChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDashboardData();
});

function initTabs() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active from all tabs and links
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active to current
            const targetTab = link.getAttribute('data-tab');
            link.classList.add('active');
            
            const tabContent = document.getElementById(targetTab);
            if (tabContent) {
                tabContent.classList.add('active');
            }
            
            // Update Title / Subtitle
            updateHeaderTitle(targetTab);

            // Re-render map if map-opt is selected
            if (targetTab === 'map-opt' && typeof window.map !== 'undefined') {
                setTimeout(() => {
                    window.map.invalidateSize();
                }, 200);
            }
        });
    });
}

function updateHeaderTitle(tab) {
    const title = document.getElementById('tab-title');
    const subtitle = document.getElementById('tab-subtitle');
    
    if (tab === 'dashboard') {
        title.innerText = 'Vessel Performance Dashboard';
        subtitle.innerText = 'Real-time analysis against Charter Party warranted standards.';
    } else if (tab === 'map-opt') {
        title.innerText = 'Voyage Optimizer & Route Planner';
        subtitle.innerText = 'Bespoke route recommendations leveraging historical weather datasets.';
    } else if (tab === 'claims') {
        title.innerText = 'Charter Party Claim Analysis';
        subtitle.innerText = 'Commercial speed and fuel compliance reports.';
    }
}

async function loadDashboardData() {
    const data = await fetchPerformanceData();
    if (!data) return;

    // Update Profile Info
    document.getElementById('vessel-name-badge').innerText = data.vessel.name;
    document.getElementById('vessel-manager').innerText = data.vessel.tech_manager;
    document.getElementById('vessel-voyage').innerText = data.vessel.voyage;

    // Update KPI Card Numbers
    const metrics = data.metrics;
    
    // Speed Variance
    const speedVarEl = document.getElementById('val-speed-var');
    const speedVarKpi = document.getElementById('kpi-speed-variance');
    speedVarEl.innerText = `${metrics.speed_variance_knots > 0 ? '+' : ''}${metrics.speed_variance_knots} kn`;
    if (metrics.speed_variance_knots < -0.3) {
        speedVarKpi.className = "kpi-card status-alert";
    } else {
        speedVarKpi.className = "kpi-card status-good";
    }
    document.getElementById('sub-speed-var').innerText = `Actual Avg: ${metrics.avg_speed_knots} kn / Warranted: ${metrics.warranted_speed_knots} kn`;

    // Fuel Variance
    const fuelVarEl = document.getElementById('val-fuel-var');
    fuelVarEl.innerText = `${metrics.fuel_variance_mt_day > 0 ? '+' : ''}${metrics.fuel_variance_mt_day} MT/day`;
    // We are consuming LESS fuel than cp warranted, which is good! So negative variance is good.
    const fuelVarKpi = document.getElementById('kpi-fuel-variance');
    if (metrics.fuel_variance_mt_day > 0.5) {
        fuelVarKpi.className = "kpi-card status-alert";
    } else {
        fuelVarKpi.className = "kpi-card status-good";
    }
    document.getElementById('sub-fuel-var').innerText = `Avg ME: ${metrics.avg_daily_me_cons} MT/day / Warranted: ${metrics.warranted_daily_cons} MT`;

    // General Status
    document.getElementById('val-status').innerText = metrics.performance_status;
    const statusKpi = document.getElementById('kpi-status');
    if (metrics.performance_status === 'UNDERPERFORMING') {
        statusKpi.className = "kpi-card status-alert";
    } else {
        statusKpi.className = "kpi-card status-good";
    }

    // Off-hire Risk
    const offhireEl = document.getElementById('val-offhire');
    const offhireKpi = document.getElementById('kpi-offhire');
    if (metrics.off_hire_risk) {
        offhireEl.innerText = 'HIGH';
        offhireKpi.className = "kpi-card status-alert";
    } else {
        offhireEl.innerText = 'LOW';
        offhireKpi.className = "kpi-card status-good";
    }

    // Build Table
    buildTable(data.daily_data);

    // Build Charts
    buildCharts(data.daily_data, data.cp_warranted);
}

function buildTable(reports) {
    const tbody = document.getElementById('noon-reports-table-body');
    tbody.innerHTML = '';

    reports.forEach(r => {
        const tr = document.createElement('tr');
        
        let statusBadge = `<span class="badge badge-info">${r.status}</span>`;
        if (r.status.includes('COSP')) statusBadge = `<span class="badge badge-success">COSP</span>`;
        if (r.status.includes('EOSP')) statusBadge = `<span class="badge badge-warning">EOSP</span>`;
        
        // Speed Variance Indicator
        let speedVarianceIndicator = '';
        if (r.status === 'At Sea') {
            const diff = r.speed_actual - r.speed_warranted;
            if (diff >= 0) {
                speedVarianceIndicator = `<span class="badge badge-success">+${diff.toFixed(1)} kn</span>`;
            } else {
                speedVarianceIndicator = `<span class="badge badge-danger">${diff.toFixed(1)} kn</span>`;
            }
        } else {
            speedVarianceIndicator = `<span style="color:var(--text-secondary);">—</span>`;
        }

        tr.innerHTML = `
            <td><strong>${r.date}</strong></td>
            <td>${statusBadge}</td>
            <td style="font-family: var(--font-mono);">${r.lat.toFixed(3)}&deg; N / ${r.lon.toFixed(3)}&deg; E</td>
            <td style="font-family: var(--font-mono);">${r.speed_actual > 0 ? r.speed_actual.toFixed(1) : '—'}</td>
            <td style="font-family: var(--font-mono);">${r.rpm > 0 ? r.rpm : '—'}</td>
            <td style="font-family: var(--font-mono);">${r.speed_actual > 0 ? r.slip_pct.toFixed(1) + '%' : '—'}</td>
            <td style="font-family: var(--font-mono);">${r.fuel_consumed_me > 0 ? r.fuel_consumed_me.toFixed(1) : '—'}</td>
            <td>
                <span class="badge ${r.wind_beaufort > 4 ? 'badge-danger' : 'badge-success'}">
                    BF ${r.wind_beaufort} (${r.wind_speed} kn ${r.wind_dir})
                </span>
            </td>
            <td>${speedVarianceIndicator}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Helper function to calculate visually balanced Y-axis limits
function calculateSmartBounds(actuals, warrants, minSpan, forceZeroMin = false) {
    const validValues = [...actuals, ...warrants].filter(v => v !== null && v !== undefined && !isNaN(v) && v > 0);
    if (validValues.length === 0) {
        return { min: forceZeroMin ? 0 : 10, max: forceZeroMin ? 15 : 20 };
    }
    
    let minVal = Math.min(...validValues);
    let maxVal = Math.max(...validValues);
    let range = maxVal - minVal;
    
    if (range < minSpan) {
        const mid = (minVal + maxVal) / 2;
        minVal = mid - minSpan / 2;
        maxVal = mid + minSpan / 2;
    } else {
        // Add 15% padding to top and bottom to prevent points from touching borders
        const padding = range * 0.15;
        minVal = minVal - padding;
        maxVal = maxVal + padding;
    }
    
    let finalMin = Math.floor(minVal);
    let finalMax = Math.ceil(maxVal);
    
    if (forceZeroMin || finalMin < 0) {
        finalMin = 0;
    }
    
    // Safety check
    if (finalMax <= finalMin) {
        finalMax = finalMin + 5;
    }
    
    return { min: finalMin, max: finalMax };
}

// Extrapolate first sea day values back to COSP to handle sparse start gap smoothly
function interpolateVoyageSegment(arr, reports) {
    const result = [...arr];
    // Find the first index where the vessel is actively steaming at sea
    let firstSeaIdx = -1;
    for (let i = 0; i < reports.length; i++) {
        if (reports[i].status === 'At Sea' && result[i] !== null && result[i] > 0) {
            firstSeaIdx = i;
            break;
        }
    }
    
    if (firstSeaIdx !== -1) {
        // Extrapolate sea values backward to any prior COSP / Port day in the voyage
        for (let i = firstSeaIdx - 1; i >= 0; i--) {
            if (reports[i].status.includes('COSP') || reports[i].status.includes('Sea')) {
                result[i] = result[firstSeaIdx];
            }
        }
    }
    return result;
}

function buildCharts(reports, cp) {
    const labels = reports.map(r => r.date);
    
    // We only warrant speed/consumption during the voyage (COSP to EOSP)
    const isVoyageDay = reports.map(r => r.status === 'At Sea' || r.status.includes('COSP') || r.status.includes('EOSP'));

    // Mapped raw data (null for port days where CP doesn't apply)
    const rawSpeedActuals = reports.map((r, idx) => (isVoyageDay[idx] && r.speed_actual > 0) ? r.speed_actual : null);
    const rawSpeedWarrants = reports.map((r, idx) => isVoyageDay[idx] ? cp.speed_knots : null);

    const rawFuelActuals = reports.map((r, idx) => (isVoyageDay[idx] && r.fuel_consumed_me > 0) ? r.fuel_consumed_me : null);
    const rawFuelWarrants = reports.map((r, idx) => isVoyageDay[idx] ? cp.fuel_consumption_mt_day : null);

    // Apply linear extrapolation/interpolation to fill COSP voyage start gap smoothly
    const speedActuals = interpolateVoyageSegment(rawSpeedActuals, reports);
    const speedWarrants = rawSpeedWarrants;

    const fuelActuals = interpolateVoyageSegment(rawFuelActuals, reports);
    const fuelWarrants = rawFuelWarrants;

    // Calculate smart limits dynamically to keep charts compact and balanced
    const speedBounds = calculateSmartBounds(speedActuals, speedWarrants, 6.0, false);
    const fuelBounds = calculateSmartBounds(fuelActuals, fuelWarrants, 15.0, false);

    // Speed Chart Options
    const speedChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: true,
        layout: {
            padding: { top: 10, bottom: 5, left: 5, right: 10 }
        },
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            },
            y: {
                min: speedBounds.min,
                max: speedBounds.max,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            }
        }
    };

    // Fuel Chart Options
    const fuelChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: true,
        layout: {
            padding: { top: 10, bottom: 5, left: 5, right: 10 }
        },
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            },
            y: {
                min: fuelBounds.min,
                max: fuelBounds.max,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            }
        }
    };

    // Speed Chart
    if (speedChartInstance) speedChartInstance.destroy();
    const speedCtx = document.getElementById('speedChart').getContext('2d');
    
    const speedGrad = speedCtx.createLinearGradient(0, 0, 0, 220);
    speedGrad.addColorStop(0, 'rgba(0, 168, 204, 0.35)');
    speedGrad.addColorStop(1, 'rgba(0, 168, 204, 0.0)');

    speedChartInstance = new Chart(speedCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Speed (knots)',
                    data: speedActuals,
                    borderColor: '#00a8cc',
                    backgroundColor: speedGrad,
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#00a8cc',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    spanGaps: true
                },
                {
                    label: 'Warranted Speed (knots)',
                    data: speedWarrants,
                    borderColor: '#ff4757',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0,
                    borderWidth: 1.5,
                    pointRadius: 0,
                    spanGaps: true
                }
            ]
        },
        options: speedChartOptions
    });

    // Fuel Chart
    if (fuelChartInstance) fuelChartInstance.destroy();
    const fuelCtx = document.getElementById('fuelChart').getContext('2d');
    
    const fuelGrad = fuelCtx.createLinearGradient(0, 0, 0, 220);
    fuelGrad.addColorStop(0, 'rgba(12, 204, 153, 0.35)');
    fuelGrad.addColorStop(1, 'rgba(12, 204, 153, 0.0)');

    fuelChartInstance = new Chart(fuelCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Cons (MT)',
                    data: fuelActuals,
                    borderColor: '#0c9',
                    backgroundColor: fuelGrad,
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#0c9',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    spanGaps: true
                },
                {
                    label: 'Warranted Cons Limit (MT)',
                    data: fuelWarrants,
                    borderColor: '#ff4757',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0,
                    borderWidth: 1.5,
                    pointRadius: 0,
                    spanGaps: true
                }
            ]
        },
        options: fuelChartOptions
    });
}

function refreshData() {
    loadDashboardData();
    if (typeof window.initMapData !== 'undefined') {
        window.initMapData();
    }
}
