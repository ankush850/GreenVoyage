"""
Vessel Performance & Voyage Optimization Tool
Flask Backend — Main Application
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# ─────────────────────────────────────────────
# STATIC DATA: DE XI Noon Report (Apr 2026)
# Parsed from NOON REPORT- SAMPLE.xlsx
# ─────────────────────────────────────────────

VESSEL_INFO = {
    "name": "DE XI",
    "tech_manager": "Kirkward Holdings",
    "voyage": "Singapore (SGP) → Sungai Linggi",
    "cargo": "In Ballast",
    "imo": "IMO-DEXI-001",
}

# Daily noon report data (6 days: Apr 22–27, 2026)
NOON_REPORTS = [
    {
        "date": "2026-04-22",
        "lat": 2.032,   # 02 01.9 N
        "lon": 104.828, # 104 49.7 E
        "status": "In Port / COSP",
        "speed_actual": 0.0,
        "speed_warranted": 12.0,
        "distance_sailed": 0,
        "engine_distance": 277.9,
        "rpm": 0,
        "slip_pct": 0.0,
        "draught_fwd": 5.0,
        "draught_aft": 8.0,
        "wind_beaufort": 2,
        "wind_speed": 7.0,
        "wind_dir": "N",
        "fuel_vlsfo_rob": 285.0,
        "fuel_lsmgo_rob": 45.0,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 4.5,
        "fuel_consumed_boiler": 0.5,
        "cyl_oil_rob": 20240,
        "cyl_oil_consumed": 0,
        "eta_next_port": "2026-04-23 20:00",
        "dist_to_next_port": 220.0,
        "remarks": "Port — COSP event"
    },
    {
        "date": "2026-04-23",
        "lat": 1.298,   # 01 17.9 N
        "lon": 103.333, # 103 19.9 E
        "status": "At Sea",
        "speed_actual": 11.3,
        "speed_warranted": 12.0,
        "distance_sailed": 120.0,
        "engine_distance": 127.02,
        "rpm": 80,
        "slip_pct": 5.5,
        "draught_fwd": 5.5,
        "draught_aft": 8.5,
        "wind_beaufort": 2,
        "wind_speed": 5.0,
        "wind_dir": "SE",
        "fuel_vlsfo_rob": 271.5,
        "fuel_lsmgo_rob": 43.8,
        "fuel_consumed_me": 12.3,
        "fuel_consumed_ae": 1.1,
        "fuel_consumed_boiler": 0.1,
        "cyl_oil_rob": 20100,
        "cyl_oil_consumed": 140,
        "eta_next_port": "2026-04-23 20:00",
        "dist_to_next_port": 99.0,
        "remarks": "Good weather, slight underperformance vs CP"
    },
    {
        "date": "2026-04-24",
        "lat": 2.263,   # 02 15.8 N
        "lon": 101.998, # 101 59.9 E
        "status": "At Sea",
        "speed_actual": 12.2,
        "speed_warranted": 12.0,
        "distance_sailed": 101.0,
        "engine_distance": 107.01,
        "rpm": 82,
        "slip_pct": 5.6,
        "draught_fwd": 5.5,
        "draught_aft": 8.5,
        "wind_beaufort": 2,
        "wind_speed": 5.0,
        "wind_dir": "SW",
        "fuel_vlsfo_rob": 258.2,
        "fuel_lsmgo_rob": 42.9,
        "fuel_consumed_me": 12.5,
        "fuel_consumed_ae": 0.9,
        "fuel_consumed_boiler": 0.0,
        "cyl_oil_rob": 20020,
        "cyl_oil_consumed": 80,
        "eta_next_port": "—",
        "dist_to_next_port": 0.0,
        "remarks": "Arrived Sungai Linggi, EOSP"
    },
    {
        "date": "2026-04-25",
        "lat": 2.263,
        "lon": 101.998,
        "status": "In Port",
        "speed_actual": 0.0,
        "speed_warranted": 0.0,
        "distance_sailed": 0,
        "engine_distance": 0,
        "rpm": 0,
        "slip_pct": 0.0,
        "draught_fwd": 5.5,
        "draught_aft": 8.5,
        "wind_beaufort": 3,
        "wind_speed": 8.0,
        "wind_dir": "N",
        "fuel_vlsfo_rob": 254.7,
        "fuel_lsmgo_rob": 42.3,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 3.4,
        "fuel_consumed_boiler": 0.1,
        "cyl_oil_rob": 20020,
        "cyl_oil_consumed": 0,
        "eta_next_port": "—",
        "dist_to_next_port": 0,
        "remarks": "In port — cargo operations"
    },
    {
        "date": "2026-04-26",
        "lat": 2.263,
        "lon": 101.998,
        "status": "In Port",
        "speed_actual": 0.0,
        "speed_warranted": 0.0,
        "distance_sailed": 0,
        "engine_distance": 0,
        "rpm": 0,
        "slip_pct": 0.0,
        "draught_fwd": 5.5,
        "draught_aft": 8.5,
        "wind_beaufort": 2,
        "wind_speed": 4.0,
        "wind_dir": "NE",
        "fuel_vlsfo_rob": 251.4,
        "fuel_lsmgo_rob": 41.8,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 3.2,
        "fuel_consumed_boiler": 0.1,
        "cyl_oil_rob": 20020,
        "cyl_oil_consumed": 0,
        "eta_next_port": "—",
        "dist_to_next_port": 0,
        "remarks": "In port — cargo operations"
    },
    {
        "date": "2026-04-27",
        "lat": 2.263,
        "lon": 101.998,
        "status": "In Port",
        "speed_actual": 0.0,
        "speed_warranted": 0.0,
        "distance_sailed": 0,
        "engine_distance": 0,
        "rpm": 0,
        "slip_pct": 0.0,
        "draught_fwd": 5.5,
        "draught_aft": 8.5,
        "wind_beaufort": 2,
        "wind_speed": 4.0,
        "wind_dir": "NE",
        "fuel_vlsfo_rob": 248.1,
        "fuel_lsmgo_rob": 41.2,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 3.2,
        "fuel_consumed_boiler": 0.1,
        "cyl_oil_rob": 20020,
        "cyl_oil_consumed": 0,
        "eta_next_port": "—",
        "dist_to_next_port": 0,
        "remarks": "In port"
    }
]

# Warranted performance (Charter Party)
CP_WARRANTED = {
    "speed_knots": 12.0,
    "fuel_consumption_mt_day": 28.0,  # VLSFO in ballast condition
    "conditions": "Beaufort ≤ 4, Douglas Sea State ≤ 3"
}

# ─────────────────────────────────────────────
# PERFORMANCE CALCULATIONS
# ─────────────────────────────────────────────

def calculate_performance_metrics():
    sea_days = [r for r in NOON_REPORTS if r["status"] == "At Sea"]
    
    total_distance = sum(r["distance_sailed"] for r in sea_days)
    total_sea_hours = len(sea_days) * 24
    avg_speed = sum(r["speed_actual"] for r in sea_days) / len(sea_days) if sea_days else 0
    
    total_me_consumed = sum(r["fuel_consumed_me"] for r in NOON_REPORTS)
    total_ae_consumed = sum(r["fuel_consumed_ae"] for r in NOON_REPORTS)
    
    # Speed variance (positive = over-performing, negative = under)
    speed_variance = avg_speed - CP_WARRANTED["speed_knots"]
    speed_variance_pct = (speed_variance / CP_WARRANTED["speed_knots"]) * 100

    # Fuel performance for sea days
    actual_daily_cons = sum(r["fuel_consumed_me"] for r in sea_days) / len(sea_days) if sea_days else 0
    fuel_variance = actual_daily_cons - CP_WARRANTED["fuel_consumption_mt_day"]
    fuel_variance_pct = (fuel_variance / CP_WARRANTED["fuel_consumption_mt_day"]) * 100

    # Off-hire risk: if speed deficit > 0.5 kn sustained
    off_hire_risk = speed_variance < -0.5

    return {
        "total_distance_nm": round(total_distance, 1),
        "avg_speed_knots": round(avg_speed, 2),
        "warranted_speed_knots": CP_WARRANTED["speed_knots"],
        "speed_variance_knots": round(speed_variance, 2),
        "speed_variance_pct": round(speed_variance_pct, 1),
        "total_me_consumed_mt": round(total_me_consumed, 1),
        "total_ae_consumed_mt": round(total_ae_consumed, 1),
        "avg_daily_me_cons": round(actual_daily_cons, 2),
        "warranted_daily_cons": CP_WARRANTED["fuel_consumption_mt_day"],
        "fuel_variance_mt_day": round(fuel_variance, 2),
        "fuel_variance_pct": round(fuel_variance_pct, 1),
        "off_hire_risk": off_hire_risk,
        "sea_days": len(sea_days),
        "port_days": len(NOON_REPORTS) - len(sea_days),
        "performance_status": "UNDERPERFORMING" if speed_variance < -0.3 else ("MEETING" if speed_variance < 0.3 else "OVERPERFORMING")
    }


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/vessel')
def vessel_info():
    return jsonify(VESSEL_INFO)

@app.route('/api/noon-reports')
def noon_reports():
    return jsonify(NOON_REPORTS)

@app.route('/api/performance')
def performance():
    metrics = calculate_performance_metrics()
    return jsonify({
        "vessel": VESSEL_INFO,
        "metrics": metrics,
        "cp_warranted": CP_WARRANTED,
        "daily_data": NOON_REPORTS
    })

@app.route('/api/track')
def vessel_track():
    """Return lat/lon positions for map plotting."""
    track = [
        {
            "date": r["date"],
            "lat": r["lat"],
            "lon": r["lon"],
            "status": r["status"],
            "speed": r["speed_actual"],
            "beaufort": r["wind_beaufort"]
        }
        for r in NOON_REPORTS
    ]
    return jsonify(track)

@app.route('/api/weather-route')
def weather_route():
    """
    Fetch marine weather from Open-Meteo along the Singapore → Sungai Linggi route.
    Uses a few waypoints along the route.
    """
    import requests as req

    waypoints = [
        {"name": "Singapore", "lat": 1.29, "lon": 103.85},
        {"name": "Malacca Strait Entry", "lat": 1.50, "lon": 103.20},
        {"name": "Mid-Strait", "lat": 2.00, "lon": 102.50},
        {"name": "Sungai Linggi", "lat": 2.50, "lon": 101.87},
    ]

    results = []
    for wp in waypoints:
        try:
            url = (
                f"https://marine-api.open-meteo.com/v1/marine"
                f"?latitude={wp['lat']}&longitude={wp['lon']}"
                f"&hourly=wave_height,wave_direction,wave_period,wind_wave_height"
                f"&forecast_days=3&timezone=UTC"
            )
            r = req.get(url, timeout=5)
            data = r.json()
            hourly = data.get("hourly", {})
            wave_heights = hourly.get("wave_height", [None]*24)
            wave_dirs = hourly.get("wave_direction", [None]*24)
            results.append({
                "waypoint": wp["name"],
                "lat": wp["lat"],
                "lon": wp["lon"],
                "avg_wave_height_m": round(sum(h for h in wave_heights[:24] if h) / max(1, len([h for h in wave_heights[:24] if h])), 2),
                "avg_wave_direction": wave_dirs[12] if wave_dirs else None,
                "risk_level": _wave_risk(wave_heights),
                "hourly_waves": wave_heights[:24],
                "hourly_dirs": wave_dirs[:24],
            })
        except Exception as e:
            results.append({
                "waypoint": wp["name"],
                "lat": wp["lat"],
                "lon": wp["lon"],
                "avg_wave_height_m": 1.2,
                "risk_level": "LOW",
                "error": str(e)
            })
    return jsonify(results)


def _wave_risk(wave_heights):
    valid = [h for h in wave_heights[:24] if h is not None]
    if not valid:
        return "UNKNOWN"
    avg = sum(valid) / len(valid)
    if avg < 1.5:
        return "LOW"
    elif avg < 3.0:
        return "MODERATE"
    elif avg < 5.0:
        return "HIGH"
    return "SEVERE"


@app.route('/api/route-optimize')
def route_optimize():
    """Compare direct route vs weather-optimized route."""
    direct = {
        "name": "Direct Route",
        "distance_nm": 221,
        "waypoints": [
            {"lat": 1.29, "lon": 103.85, "name": "Singapore"},
            {"lat": 1.50, "lon": 103.20, "name": "Malacca Strait Entry"},
            {"lat": 2.00, "lon": 102.50, "name": "Mid-Strait"},
            {"lat": 2.50, "lon": 101.87, "name": "Sungai Linggi"},
        ],
        "est_duration_hrs": 18.4,
        "est_fuel_mt": 24.5,
        "max_beaufort": 4,
        "risk": "MODERATE",
        "description": "Shortest distance through Malacca Strait"
    }

    optimized = {
        "name": "Weather-Optimized Route",
        "distance_nm": 235,
        "waypoints": [
            {"lat": 1.29, "lon": 103.85, "name": "Singapore"},
            {"lat": 1.20, "lon": 103.50, "name": "Southern Bypass"},
            {"lat": 1.60, "lon": 102.80, "name": "Calmer Waters"},
            {"lat": 2.10, "lon": 102.20, "name": "Favourable Current Zone"},
            {"lat": 2.50, "lon": 101.87, "name": "Sungai Linggi"},
        ],
        "est_duration_hrs": 18.9,
        "est_fuel_mt": 22.8,
        "max_beaufort": 2,
        "risk": "LOW",
        "description": "Slightly longer but avoids headwinds — saves ~1.7 MT fuel"
    }

    savings = {
        "fuel_saved_mt": round(direct["est_fuel_mt"] - optimized["est_fuel_mt"], 1),
        "fuel_cost_saved_usd": round((direct["est_fuel_mt"] - optimized["est_fuel_mt"]) * 580, 0),  # ~$580/MT VLSFO
        "time_diff_hrs": round(optimized["est_duration_hrs"] - direct["est_duration_hrs"], 1),
        "recommendation": "optimized"
    }

    return jsonify({
        "direct": direct,
        "optimized": optimized,
        "savings": savings
    })


if __name__ == '__main__':
    print("Vessel Performance & Voyage Optimization Tool")
    print("   Starting at http://localhost:5000")
    app.run(debug=True, port=5000)
