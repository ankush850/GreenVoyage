// Dashboard Controller
let speedChartInstance = null;
let fuelChartInstance = null;

// Official 10-Page Report variables
let rLSFOConsChart = null;
let rLSFOROBChart = null;
let rSpeedChart = null;
let rMGOROBChart = null;
let rTimeUtilChart = null;
let rFuelUtilChart = null;
let rBeaufortChart = null;
let rWindChart = null;
let rWaveChart = null;
let rCurrentChart = null;
let windowReportMap = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initReportMenu();
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

            // Load Official Report Data if selected
            if (targetTab === 'official-report') {
                loadOfficialReportData();
            }
        });
    });
}

function initReportMenu() {
    const menuItems = document.querySelectorAll('.report-menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.report-menu-item').forEach(m => m.classList.remove('active'));
            document.querySelectorAll('.report-page').forEach(p => p.classList.remove('active'));
            
            item.classList.add('active');
            const pageId = item.getAttribute('data-page');
            const pageEl = document.getElementById(pageId);
            if (pageEl) {
                pageEl.classList.add('active');
            }
            
            // Re-render Page 10 Leaflet map
            if (pageId === 'page10' && windowReportMap) {
                setTimeout(() => {
                    windowReportMap.invalidateSize();
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
    } else if (tab === 'official-report') {
        title.innerText = 'Official Voyage Report';
        subtitle.innerText = 'Confidential Vessel Performance Report (Singapore EOPL to Sungai Linggi)';
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

async function loadOfficialReportData() {
    const response = await fetch('/api/performance');
    const data = await response.json();
    if (!data) return;

    const reports = data.daily_data;
    const cp = data.cp_warranted;

    // ─────────────────────────────────────────────
    // Page 3: Master Noon Report Table
    // ─────────────────────────────────────────────
    const noonBody = document.getElementById('report-noon-table-body');
    if (noonBody) {
        noonBody.innerHTML = '';
        reports.forEach(r => {
            const tr = document.createElement('tr');
            if (r.operation.includes('Manoeuvring')) {
                tr.className = 'highlight-row';
            }
            tr.innerHTML = `
                <td><strong>${r.date.substring(5)}</strong></td>
                <td>${r.lat.toFixed(2)} N</td>
                <td>${r.lon.toFixed(2)} E</td>
                <td>${r.operation}</td>
                <td>${r.condition}</td>
                <td>${r.steaming_hrs > 0 ? r.steaming_hrs.toFixed(1) : '—'}</td>
                <td>${r.distance_sailed > 0 ? r.distance_sailed.toFixed(2) : '—'}</td>
                <td>${r.speed_actual > 0 ? r.speed_actual.toFixed(2) : '—'}</td>
                <td>${r.speed_warranted.toFixed(1)}</td>
                <td>${r.rpm > 0 ? r.rpm : '—'}</td>
                <td>${r.speed_actual > 0 ? r.slip_pct.toFixed(1) + '%' : '—'}</td>
                <td>${r.wind_dir}</td>
                <td>${r.wind_beaufort > 0 ? 'BF ' + r.wind_beaufort : '—'}</td>
                <td>${r.wave_height > 0 ? r.wave_height + 'm' : '—'}</td>
                <td>${r.current_speed > 0 ? r.current_dir + ' / ' + r.current_speed + ' kn' : '—'}</td>
            `;
            noonBody.appendChild(tr);
        });
    }

    // ─────────────────────────────────────────────
    // Page 4: Engine Summary (ROB) Table
    // ─────────────────────────────────────────────
    const engineBody = document.getElementById('report-engine-table-body');
    if (engineBody) {
        engineBody.innerHTML = '';
        
        let totalStm = 0, totalDist = 0, totalME_lsfo = 0, totalAE_lsfo = 0, totalBoil_lsfo = 0, totalAE_mgo = 0, totalFW = 0;
        
        reports.forEach(r => {
            const tr = document.createElement('tr');
            
            totalStm += r.steaming_hrs;
            totalDist += r.distance_sailed;
            totalME_lsfo += r.fuel_consumed_me;
            totalAE_lsfo += r.fuel_consumed_ae;
            totalBoil_lsfo += r.fuel_consumed_boiler;
            totalAE_mgo += r.fuel_consumed_ae_mgo;
            totalFW += r.fw_consumed;

            tr.innerHTML = `
                <td><strong>${r.date.substring(5)}</strong></td>
                <td>${r.operation}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_vlsfo_rob.toFixed(2)}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_lsmgo_rob.toFixed(2)}</td>
                <td>${r.steaming_hrs > 0 ? '—' : cp.idle_warranted.toFixed(1)}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_me > 0 ? r.fuel_consumed_me.toFixed(3) : '—'}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_ae.toFixed(2)}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_boiler.toFixed(2)}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_me_mgo > 0 ? r.fuel_consumed_me_mgo.toFixed(2) : '—'}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_ae_mgo > 0 ? r.fuel_consumed_ae_mgo.toFixed(2) : '—'}</td>
                <td style="font-family: var(--font-mono);">${r.fw_consumed.toFixed(1)}</td>
                <td style="font-family: var(--font-mono);">${r.fw_rob.toFixed(1)}</td>
            `;
            engineBody.appendChild(tr);
        });

        // Append Totals row for Page 4
        const tRow4 = document.createElement('tr');
        tRow4.className = 'total-row';
        tRow4.innerHTML = `
            <td><strong>TOTAL</strong></td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td style="font-family: var(--font-mono);">${totalME_lsfo.toFixed(3)}</td>
            <td style="font-family: var(--font-mono);">${totalAE_lsfo.toFixed(2)}</td>
            <td style="font-family: var(--font-mono);">${totalBoil_lsfo.toFixed(2)}</td>
            <td>—</td>
            <td style="font-family: var(--font-mono);">${totalAE_mgo.toFixed(3)}</td>
            <td style="font-family: var(--font-mono);">${totalFW.toFixed(1)}</td>
            <td>—</td>
        `;
        engineBody.appendChild(tRow4);
    }

    // ─────────────────────────────────────────────
    // Page 6: Engine Cons & ROB Table
    // ─────────────────────────────────────────────
    const consBody = document.getElementById('report-cons-table-body');
    if (consBody) {
        consBody.innerHTML = '';
        let totalStm = 0, totalDist = 0, totalME_lsfo = 0, totalAE_lsfo = 0, totalBoil_lsfo = 0, totalAE_mgo = 0;
        
        reports.forEach(r => {
            const tr = document.createElement('tr');
            const totalDayLSFO = r.fuel_consumed_me + r.fuel_consumed_ae + r.fuel_consumed_boiler;
            const totalDayMGO = r.fuel_consumed_me_mgo + r.fuel_consumed_ae_mgo + r.fuel_consumed_boiler_mgo;
            
            totalStm += r.steaming_hrs;
            totalDist += r.distance_sailed;
            totalME_lsfo += r.fuel_consumed_me;
            totalAE_lsfo += r.fuel_consumed_ae;
            totalBoil_lsfo += r.fuel_consumed_boiler;
            totalAE_mgo += r.fuel_consumed_ae_mgo;

            tr.innerHTML = `
                <td><strong>${r.date.substring(5)}</strong></td>
                <td>${r.operation}</td>
                <td>${r.steaming_hrs > 0 ? r.steaming_hrs.toFixed(1) : '—'}</td>
                <td>${r.distance_sailed > 0 ? r.distance_sailed.toFixed(2) : '—'}</td>
                <td>${r.speed_actual > 0 ? r.speed_actual.toFixed(1) : '—'}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_me > 0 ? r.fuel_consumed_me.toFixed(3) : '—'}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_ae.toFixed(3)}</td>
                <td style="font-family: var(--font-mono);">${r.fuel_consumed_boiler.toFixed(2)}</td>
                <td style="font-family: var(--font-mono);">${totalDayLSFO.toFixed(3)}</td>
                <td style="font-family: var(--font-mono);">${totalDayMGO.toFixed(3)}</td>
                <td>${r.rpm > 0 ? r.rpm : '—'}</td>
                <td style="max-width:180px; text-overflow:ellipsis; overflow:hidden;">${r.remarks}</td>
            `;
            consBody.appendChild(tr);
        });

        // Append Totals row for Page 6
        const tRow6 = document.createElement('tr');
        tRow6.className = 'total-row';
        tRow6.innerHTML = `
            <td><strong>TOTAL</strong></td>
            <td>—</td>
            <td>${totalStm.toFixed(1)}</td>
            <td>${totalDist.toFixed(2)}</td>
            <td>10.35</td>
            <td style="font-family: var(--font-mono);">${totalME_lsfo.toFixed(3)}</td>
            <td style="font-family: var(--font-mono);">${totalAE_lsfo.toFixed(3)}</td>
            <td style="font-family: var(--font-mono);">${totalBoil_lsfo.toFixed(2)}</td>
            <td style="font-family: var(--font-mono);">${(totalME_lsfo + totalAE_lsfo + totalBoil_lsfo).toFixed(3)}</td>
            <td style="font-family: var(--font-mono);">${totalAE_mgo.toFixed(3)}</td>
            <td>—</td>
            <td>—</td>
        `;
        consBody.appendChild(tRow6);
    }

    // Render charts
    buildPage7Charts(reports, cp);
    buildPage8Charts();
    buildPage9Charts(reports);
    buildPage10Map(reports);
}

function buildPage7Charts(reports, cp) {
    const labels = reports.map(r => r.date.substring(5));
    const lsfoCons = reports.map(r => r.fuel_consumed_me + r.fuel_consumed_ae + r.fuel_consumed_boiler);
    const lsfoROB = reports.map(r => r.fuel_vlsfo_rob);
    const speeds = reports.map(r => r.speed_actual > 0 ? r.speed_actual : null);
    const mgoROB = reports.map(r => r.fuel_lsmgo_rob);

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } }
        }
    };

    // Chart 7A: Daily LSFO Cons vs CP Limit
    if (rLSFOConsChart) rLSFOConsChart.destroy();
    const ctxA = document.getElementById('reportLSFOConsChart').getContext('2d');
    if (ctxA) {
        rLSFOConsChart = new Chart(ctxA, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual LSFO Cons (MT)',
                        data: lsfoCons,
                        backgroundColor: '#0c9',
                        borderRadius: 4
                    },
                    {
                        label: 'CP Warranted Limit (5.5 MT/D)',
                        data: Array(reports.length).fill(cp.idle_warranted),
                        type: 'line',
                        borderColor: '#ff4757',
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: commonOptions
        });
    }

    // Chart 7B: LSFO ROB Drawdown
    if (rLSFOROBChart) rLSFOROBChart.destroy();
    const ctxB = document.getElementById('reportLSFOROBChart').getContext('2d');
    if (ctxB) {
        rLSFOROBChart = new Chart(ctxB, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: lsfoROB,
                    borderColor: '#00a8cc',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.2,
                    pointRadius: 3
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    x: commonOptions.scales.x,
                    y: { min: 920, max: 980, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } }
                }
            }
        });
    }

    // Chart 7C: Speed Profile
    if (rSpeedChart) rSpeedChart.destroy();
    const ctxC = document.getElementById('reportSpeedChart').getContext('2d');
    if (ctxC) {
        rSpeedChart = new Chart(ctxC, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual Speed',
                        data: speeds,
                        borderColor: '#00a8cc',
                        borderWidth: 2.5,
                        spanGaps: true,
                        pointRadius: 4,
                        fill: false
                    },
                    {
                        label: 'Warranted Speed (12.5)',
                        data: Array(reports.length).fill(cp.speed_knots),
                        borderColor: '#ff4757',
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                ...commonOptions,
                scales: {
                    x: commonOptions.scales.x,
                    y: { min: 8, max: 15, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } }
                }
            }
        });
    }

    // Chart 7D: MGO ROB Curve
    if (rMGOROBChart) rMGOROBChart.destroy();
    const ctxD = document.getElementById('reportMGOROBChart').getContext('2d');
    if (ctxD) {
        rMGOROBChart = new Chart(ctxD, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: mgoROB,
                    borderColor: '#eccc68',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 3
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    x: commonOptions.scales.x,
                    y: { min: 240, max: 250, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } }
                }
            }
        });
    }
}

function buildPage8Charts() {
    // Chart 8A: Voyage Time Utilisation (9 Days)
    if (rTimeUtilChart) rTimeUtilChart.destroy();
    const ctxA = document.getElementById('reportTimeUtilChart').getContext('2d');
    if (ctxA) {
        rTimeUtilChart = new Chart(ctxA, {
            type: 'doughnut',
            data: {
                labels: ['Idle – Sungai Linggi (67%)', 'Manoeuvring / Transit (22%)', 'Idle – Singapore EOPL (11%)'],
                datasets: [{
                    data: [67, 22, 11],
                    backgroundColor: ['#00a8cc', '#0c9', '#ffa502'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#9ca3af', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // Chart 8B: LSFO Consumption by System (46.99 MT)
    if (rFuelUtilChart) rFuelUtilChart.destroy();
    const ctxB = document.getElementById('reportFuelUtilChart').getContext('2d');
    if (ctxB) {
        rFuelUtilChart = new Chart(ctxB, {
            type: 'doughnut',
            data: {
                labels: ['Aux. Engines (53%)', 'Main Engine (27%)', 'Boiler (20%)'],
                datasets: [{
                    data: [53, 27, 20],
                    backgroundColor: ['#0c9', '#00a8cc', '#ff4757'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#9ca3af', font: { size: 10 } }
                    }
                }
            }
        });
    }
}

function buildPage9Charts(reports) {
    const labels = reports.map(r => r.date.substring(5));
    const reportedBF = reports.map(r => r.wind_beaufort);
    // Mock comparison
    const actualBF = reports.map((r, i) => Math.max(0, r.wind_beaufort + (i % 2 === 0 ? 0.3 : -0.2)));
    
    const windSpdRep = reports.map(r => r.wind_speed);
    const windSpdAct = reports.map((r, i) => Math.max(0, r.wind_speed + (i % 2 === 0 ? 1.5 : -1.2)));

    const waveAct = reports.map(r => r.wave_height > 0 ? r.wave_height : null);
    const swellAct = reports.map(r => r.swell_height > 0 ? r.swell_height : null);

    const currentAct = reports.map(r => r.current_speed);

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#9ca3af', font: { size: 9 } } } },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 8 } } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 8 } } }
        }
    };

    // Chart 9A: Beaufort reported vs actual
    if (rBeaufortChart) rBeaufortChart.destroy();
    const ctxA = document.getElementById('reportBeaufortChart').getContext('2d');
    if (ctxA) {
        rBeaufortChart = new Chart(ctxA, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'BF Reported', data: reportedBF, borderColor: '#00a8cc', fill: false, borderWidth: 2 },
                    { label: 'BF Actual', data: actualBF, borderColor: '#ffa502', fill: false, borderWidth: 1.5, borderDash: [3, 3] }
                ]
            },
            options: commonOptions
        });
    }

    // Chart 9B: Wind Speed reported vs actual
    if (rWindChart) rWindChart.destroy();
    const ctxB = document.getElementById('reportWindChart').getContext('2d');
    if (ctxB) {
        rWindChart = new Chart(ctxB, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Reported Wind (kts)', data: windSpdRep, borderColor: '#ff4757', fill: false, borderWidth: 2 },
                    { label: 'Actual Wind (kts)', data: windSpdAct, borderColor: '#0c9', fill: false, borderWidth: 1.5 }
                ]
            },
            options: commonOptions
        });
    }

    // Chart 9C: Wave vs Swell actual
    if (rWaveChart) rWaveChart.destroy();
    const ctxC = document.getElementById('reportWaveChart').getContext('2d');
    if (ctxC) {
        rWaveChart = new Chart(ctxC, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Wave Height (m)', data: waveAct, borderColor: '#ffa502', fill: false, spanGaps: true },
                    { label: 'Swell Height (m)', data: swellAct, borderColor: '#00a8cc', fill: false, spanGaps: true }
                ]
            },
            options: commonOptions
        });
    }

    // Chart 9D: Current Speed actual
    if (rCurrentChart) rCurrentChart.destroy();
    const ctxD = document.getElementById('reportCurrentChart').getContext('2d');
    if (ctxD) {
        rCurrentChart = new Chart(ctxD, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{ label: 'Current Speed (kts)', data: currentAct, borderColor: '#0c9', fill: true, backgroundColor: 'rgba(12,204,153,0.1)' }]
            },
            options: commonOptions
        });
    }
}

function buildPage10Map(reports) {
    if (windowReportMap) return; // avoid re-initialization
    const mapContainer = document.getElementById('reportMap');
    if (!mapContainer) return;

    windowReportMap = L.map('reportMap', {
        zoomControl: true,
        attributionControl: false
    }).setView([1.75, 103.0], 8);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(windowReportMap);

    const latLns = [];
    reports.forEach((r, idx) => {
        latLns.push([r.lat, r.lon]);

        const tooltipText = `<strong>Noon Position #${idx + 1}</strong><br/>Date: ${r.date}<br/>Operation: ${r.operation}<br/>Wind Force: BF ${r.wind_beaufort}`;
        
        L.circleMarker([r.lat, r.lon], {
            radius: 6,
            fillColor: r.status === 'At Sea' ? '#00a8cc' : '#ffa502',
            color: '#fff',
            weight: 1,
            fillOpacity: 0.8
        }).bindPopup(tooltipText).addTo(windowReportMap);
    });

    L.polyline(latLns, {
        color: 'rgba(12, 204, 153, 0.6)',
        weight: 3
    }).addTo(windowReportMap);
}

function refreshData() {
    loadDashboardData();
    loadOfficialReportData();
    if (typeof window.initMapData !== 'undefined') {
        window.initMapData();
    }
}
