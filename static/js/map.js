// Interactive Map and Optimization Module
let map;
let trackLayerGroup;
let routeLayerGroup;
let optimizedRouteData = null;
let activeRouteType = 'direct'; // 'direct' or 'optimized'

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initMapData();
});

function initMap() {
    // Center the map in Malacca Strait / Singapore area
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([1.75, 103.0], 8);

    // Add stunning dark mode tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(map);

    trackLayerGroup = L.layerGroup().addTo(map);
    routeLayerGroup = L.layerGroup().addTo(map);
    
    window.map = map; // expose globally
}

async function initMapData() {
    trackLayerGroup.clearLayers();
    routeLayerGroup.clearLayers();

    // 1. Fetch and plot Vessel track (past noon reports)
    const trackPoints = await fetchVesselTrack();
    if (trackPoints && trackPoints.length > 0) {
        const latLns = trackPoints.map(p => [p.lat, p.lon]);
        
        // Plot historical points
        trackPoints.forEach((p, idx) => {
            let label = `<strong>Report Date:</strong> ${p.date}<br/>`;
            label += `<strong>Status:</strong> ${p.status}<br/>`;
            if (p.speed > 0) label += `<strong>Speed:</strong> ${p.speed} kn<br/>`;
            label += `<strong>Wind Force:</strong> Beaufort ${p.beaufort}`;

            const color = p.status.includes('COSP') ? '#0c9' : (p.status.includes('EOSP') ? '#ffa502' : '#00a8cc');
            L.circleMarker([p.lat, p.lon], {
                radius: idx === 0 || idx === trackPoints.length - 1 ? 7 : 5,
                fillColor: color,
                color: '#fff',
                weight: 1,
                fillOpacity: 0.8
            }).bindPopup(label).addTo(trackLayerGroup);
        });

        // Connect historical points with a path
        L.polyline(latLns, {
            color: 'rgba(0, 168, 204, 0.4)',
            weight: 3,
            dashArray: '5, 5'
        }).addTo(trackLayerGroup);
    }

    // 2. Fetch and render route optimization suggestions
    optimizedRouteData = await fetchRouteOptimization();
    if (optimizedRouteData) {
        renderRoutesOnMap();
        updateSavingsPanel();
        updateRouteDetailsPanel();
    }

    // 3. Fetch weather along the route
    const weatherData = await fetchWeatherAlongRoute();
    if (weatherData) {
        renderWeatherPanel(weatherData);
        // Plot weather stations on map
        weatherData.forEach(w => {
            let desc = `<strong>${w.waypoint} Wave Station</strong><br/>`;
            desc += `Avg Wave: ${w.avg_wave_height_m}m<br/>`;
            desc += `Risk Level: <span class="badge ${w.risk_level === 'LOW' ? 'badge-success' : 'badge-warning'}">${w.risk_level}</span>`;

            L.circleMarker([w.lat, w.lon], {
                radius: 4,
                fillColor: w.risk_level === 'LOW' ? '#0c9' : '#ffa502',
                color: '#111',
                weight: 1,
                fillOpacity: 0.6
            }).bindPopup(desc).addTo(routeLayerGroup);
        });
    }
}

function renderRoutesOnMap() {
    routeLayerGroup.clearLayers();
    if (!optimizedRouteData) return;

    const directPoints = optimizedRouteData.direct.waypoints.map(w => [w.lat, w.lon]);
    const optimizedPoints = optimizedRouteData.optimized.waypoints.map(w => [w.lat, w.lon]);

    // Direct Route Line
    const directPolyline = L.polyline(directPoints, {
        color: '#ff4757',
        weight: activeRouteType === 'direct' ? 4 : 2,
        opacity: activeRouteType === 'direct' ? 0.9 : 0.4,
        dashArray: activeRouteType === 'direct' ? null : '3, 6'
    }).addTo(routeLayerGroup);
    
    directPolyline.bindPopup("<strong>Direct Route</strong><br/>Estimated fuel: 24.5 MT<br/>Weather Risk: Moderate");

    // Weather Optimized Route Line
    const optPolyline = L.polyline(optimizedPoints, {
        color: '#0c9',
        weight: activeRouteType === 'optimized' ? 4 : 2,
        opacity: activeRouteType === 'optimized' ? 0.9 : 0.4,
        dashArray: activeRouteType === 'optimized' ? null : '3, 6'
    }).addTo(routeLayerGroup);
    
    optPolyline.bindPopup("<strong>Weather-Optimized Route</strong><br/>Estimated fuel: 22.8 MT<br/>Weather Risk: Low (Headwind avoidance)");

    // Zoom map bounds to routes
    const allBounds = L.latLngBounds([...directPoints, ...optimizedPoints]);
    map.fitBounds(allBounds, { padding: [30, 30] });
}

function toggleRoute(routeType) {
    activeRouteType = routeType;
    
    // Toggle active classes
    document.getElementById('opt-direct').classList.toggle('active', routeType === 'direct');
    document.getElementById('opt-optimized').classList.toggle('active', routeType === 'optimized');

    renderRoutesOnMap();
    updateRouteDetailsPanel();
}

function updateSavingsPanel() {
    if (!optimizedRouteData) return;
    const savings = optimizedRouteData.savings;
    document.getElementById('opt-savings-val').innerText = `${savings.fuel_saved_mt} MT Fuel`;
    document.getElementById('opt-dollars-saved').innerText = `$${savings.fuel_cost_saved_usd} USD`;
    document.getElementById('opt-co2-saved').innerText = `${(savings.fuel_saved_mt * 3.11).toFixed(1)}t CO₂`;
}

function updateRouteDetailsPanel() {
    if (!optimizedRouteData) return;
    const route = activeRouteType === 'direct' ? optimizedRouteData.direct : optimizedRouteData.optimized;
    
    document.getElementById('opt-summary-duration').innerText = `${route.est_duration_hrs} hrs`;
    document.getElementById('opt-summary-fuel').innerText = `${route.est_fuel_mt} MT`;
    document.getElementById('opt-summary-wave').innerText = activeRouteType === 'direct' ? '1.4m' : '0.8m';
    document.getElementById('opt-summary-wave').className = activeRouteType === 'direct' ? 'badge badge-warning' : 'badge badge-success';
    document.getElementById('opt-summary-weather').innerText = activeRouteType === 'direct' ? 'BF 4' : 'BF 2';
    document.getElementById('route-meta-overlay').innerText = `${route.name} (${route.distance_nm} NM)`;
}

function renderWeatherPanel(weatherData) {
    const weatherPanel = document.getElementById('weather-status-panel');
    if (!weatherData || weatherData.length === 0) {
        weatherPanel.innerHTML = '<span style="color:var(--accent);">Failed to load weather. Showing simulation data.</span>';
        return;
    }

    let html = '<div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">';
    weatherData.forEach(w => {
        const badgeColor = w.risk_level === 'LOW' ? 'badge-success' : 'badge-warning';
        html += `
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:0.4rem 0.6rem; border-radius:6px; border:1px solid var(--card-border);">
                <div>
                    <strong style="color:#fff;">${w.waypoint}</strong><br/>
                    <span style="font-size:0.75rem;">Wave Ht: ${w.avg_wave_height_m}m</span>
                </div>
                <span class="badge ${badgeColor}">${w.risk_level} RISK</span>
            </div>
        `;
    });
    html += '</div>';
    weatherPanel.innerHTML = html;
}

window.initMapData = initMapData;
window.toggleRoute = toggleRoute;
