// API Service module for Vessel Performance Dashboard
const API_BASE = '';

async function fetchPerformanceData() {
    try {
        const response = await fetch(`${API_BASE}/api/performance`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching performance metrics:", error);
        return null;
    }
}

async function fetchVesselTrack() {
    try {
        const response = await fetch(`${API_BASE}/api/track`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching vessel track:", error);
        return [];
    }
}

async function fetchRouteOptimization() {
    try {
        const response = await fetch(`${API_BASE}/api/route-optimize`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching route optimization:", error);
        return null;
    }
}

async function fetchWeatherAlongRoute() {
    try {
        const response = await fetch(`${API_BASE}/api/weather-route`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching weather details:", error);
        return [];
    }
}
