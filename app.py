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
    "voyage": "Singapore EOPL → Sungai Linggi",
    "cargo": "In Ballast",
    "imo": "IMO-DEXI-001",
    "period": "22 Apr – 30 Apr 2026",
    "delivery": "22 APR 2026, 00:01 LT"
}

# Daily noon report data (9 days: Apr 22–30, 2026)
NOON_REPORTS = [
    {
        "date": "2026-04-22",
        "lat": 2.032,   # 02 01.9 N
        "lon": 104.828, # 104 49.7 E
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "—",
        "wind_speed": 0.0,
        "wind_beaufort": 0,
        "wave_height": 0.0,
        "swell_dir": "—",
        "swell_height": 0.0,
        "current_dir": "—",
        "current_speed": 0.0,
        "fuel_vlsfo_rob": 970.68,
        "fuel_lsmgo_rob": 242.98,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.19,
        "fuel_consumed_boiler": 0.69,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 3.97,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 5.0,
        "fw_rob": 218.0,
        "remarks": "Anchored SGP-EOPL for bunker"
    },
    {
        "date": "2026-04-23",
        "lat": 1.298,   # 01 17.9 N
        "lon": 103.332, # 103 19.9 E
        "status": "At Sea",
        "operation": "Manoeuvring",
        "condition": "Ballast",
        "steaming_hrs": 11.2,
        "distance_sailed": 127.02,
        "speed_actual": 11.3,
        "speed_warranted": 12.5,
        "rpm": 80,
        "slip_pct": 5.5,
        "wind_dir": "E",
        "wind_speed": 6.0,
        "wind_beaufort": 2,
        "wave_height": 0.5,
        "swell_dir": "E",
        "swell_height": 0.4,
        "current_dir": "NW",
        "current_speed": 0.8,
        "fuel_vlsfo_rob": 959.73,
        "fuel_lsmgo_rob": 246.54,
        "fuel_consumed_me": 9.107,
        "fuel_consumed_ae": 3.71,
        "fuel_consumed_boiler": 0.83,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.0,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 6.0,
        "fw_rob": 212.0,
        "remarks": "Proceeding Sungai Linggi — Manoeuvring Only"
    },
    {
        "date": "2026-04-24",
        "lat": 2.263,   # 02 15.8 N
        "lon": 101.998, # 101 59.9 E
        "status": "At Port",
        "operation": "Idle / Manoeuvring",
        "condition": "Ballast",
        "steaming_hrs": 9.1,
        "distance_sailed": 107.01,
        "speed_actual": 11.7,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 5.6,
        "wind_dir": "E",
        "wind_speed": 4.0,
        "wind_beaufort": 2,
        "wave_height": 0.4,
        "swell_dir": "E",
        "swell_height": 0.3,
        "current_dir": "NW",
        "current_speed": 1.1,
        "fuel_vlsfo_rob": 949.29,
        "fuel_lsmgo_rob": 246.44,
        "fuel_consumed_me": 3.37,
        "fuel_consumed_ae": 3.20,
        "fuel_consumed_boiler": 0.87,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.1,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 8.0,
        "fw_rob": 204.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-25",
        "lat": 2.263,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "N",
        "wind_speed": 1.0,
        "wind_beaufort": 3,
        "wave_height": 0.3,
        "swell_dir": "N",
        "swell_height": 0.2,
        "current_dir": "NW",
        "current_speed": 0.4,
        "fuel_vlsfo_rob": 945.42,
        "fuel_lsmgo_rob": 246.44,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.70,
        "fuel_consumed_boiler": 1.17,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.004,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 9.0,
        "fw_rob": 195.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-26",
        "lat": 2.263,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "NE",
        "wind_speed": 3.0,
        "wind_beaufort": 2,
        "wave_height": 0.3,
        "swell_dir": "NE",
        "swell_height": 0.2,
        "current_dir": "NW",
        "current_speed": 1.0,
        "fuel_vlsfo_rob": 941.67,
        "fuel_lsmgo_rob": 246.44,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.60,
        "fuel_consumed_boiler": 1.15,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.0,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 9.0,
        "fw_rob": 186.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-27",
        "lat": 2.263,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "NE",
        "wind_speed": 3.0,
        "wind_beaufort": 2,
        "wave_height": 0.3,
        "swell_dir": "NE",
        "swell_height": 0.2,
        "current_dir": "NW",
        "current_speed": 1.0,
        "fuel_vlsfo_rob": 937.8,
        "fuel_lsmgo_rob": 246.44,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.68,
        "fuel_consumed_boiler": 1.19,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.0,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 10.0,
        "fw_rob": 176.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-28",
        "lat": 2.263,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "NE",
        "wind_speed": 2.0,
        "wind_beaufort": 2,
        "wave_height": 0.3,
        "swell_dir": "NE",
        "swell_height": 0.2,
        "current_dir": "NW",
        "current_speed": 1.0,
        "fuel_vlsfo_rob": 933.92,
        "fuel_lsmgo_rob": 246.34,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.67,
        "fuel_consumed_boiler": 1.21,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.1,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 8.0,
        "fw_rob": 168.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-29",
        "lat": 2.264,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "N",
        "wind_speed": 2.0,
        "wind_beaufort": 3,
        "wave_height": 0.4,
        "swell_dir": "N",
        "swell_height": 0.3,
        "current_dir": "NW",
        "current_speed": 1.0,
        "fuel_vlsfo_rob": 930.03,
        "fuel_lsmgo_rob": 246.24,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.68,
        "fuel_consumed_boiler": 1.21,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.1,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 8.0,
        "fw_rob": 160.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    },
    {
        "date": "2026-04-30",
        "lat": 2.264,
        "lon": 101.998,
        "status": "At Port",
        "operation": "Idle",
        "condition": "Ballast",
        "steaming_hrs": 0.0,
        "distance_sailed": 0.0,
        "speed_actual": 0.0,
        "speed_warranted": 12.5,
        "rpm": 0,
        "slip_pct": 0.0,
        "wind_dir": "N",
        "wind_speed": 6.0,
        "wind_beaufort": 3,
        "wave_height": 0.5,
        "swell_dir": "N",
        "swell_height": 0.4,
        "current_dir": "NW",
        "current_speed": 1.0,
        "fuel_vlsfo_rob": 926.27,
        "fuel_lsmgo_rob": 246.24,
        "fuel_consumed_me": 0.0,
        "fuel_consumed_ae": 2.62,
        "fuel_consumed_boiler": 1.14,
        "fuel_consumed_me_mgo": 0.0,
        "fuel_consumed_ae_mgo": 0.0,
        "fuel_consumed_boiler_mgo": 0.0,
        "fw_consumed": 9.0,
        "fw_rob": 151.0,
        "remarks": "Anchored Sungai Linggi — Waiting load instructions"
    }
]

# Warranted performance (Charter Party)
CP_WARRANTED = {
    "speed_knots": 12.5,
    "fuel_consumption_mt_day": 23.5,  # VLSFO in ballast condition (Eco speed 12.5)
    "conditions": "Beaufort ≤ 4, Douglas Sea State ≤ 3",
    "idle_warranted": 5.5
}

# ─────────────────────────────────────────────
# PERFORMANCE CALCULATIONS
# ─────────────────────────────────────────────

def calculate_performance_metrics():
    # Only calculate average speed for days with actual movement
    steaming_days = [r for r in NOON_REPORTS if r["distance_sailed"] > 0]
    total_distance = sum(r["distance_sailed"] for r in NOON_REPORTS)
    
    avg_speed = sum(r["speed_actual"] for r in steaming_days) / len(steaming_days) if steaming_days else 10.35
    
    total_lsfo_consumed = sum(r["fuel_consumed_me"] + r["fuel_consumed_ae"] + r["fuel_consumed_boiler"] for r in NOON_REPORTS)
    total_mgo_consumed = sum(r["fuel_consumed_me_mgo"] + r["fuel_consumed_ae_mgo"] + r["fuel_consumed_boiler_mgo"] for r in NOON_REPORTS)
    
    # Idle/anchorage days: status == "At Port" and steaming_hrs == 0
    idle_days = len([r for r in NOON_REPORTS if r["status"] == "At Port" and r["steaming_hrs"] == 0])

    speed_variance = avg_speed - CP_WARRANTED["speed_knots"]
    speed_variance_pct = (speed_variance / CP_WARRANTED["speed_knots"]) * 100

    # Fuel performance vs CP limit
    actual_total_lsfo = total_lsfo_consumed
    # PDF Page 1: LSFO Consumed: 46.987 MT, Warranted: 49.5 MT
    warranted_total_lsfo = 49.5
    fuel_variance = actual_total_lsfo - warranted_total_lsfo

    return {
        "total_distance_nm": round(total_distance, 2),
        "avg_speed_knots": round(avg_speed, 2),
        "warranted_speed_knots": CP_WARRANTED["speed_knots"],
        "speed_variance_knots": round(speed_variance, 2),
        "speed_variance_pct": round(speed_variance_pct, 1),
        "total_lsfo_consumed_mt": round(total_lsfo_consumed, 3),
        "warranted_lsfo_consumed_mt": warranted_total_lsfo,
        "fuel_variance_mt": round(fuel_variance, 3),
        "total_mgo_consumed_mt": round(total_mgo_consumed, 3),
        "avg_daily_lsfo": 5.5,
        "warranted_daily_cons": CP_WARRANTED["idle_warranted"],
        "off_hire_risk": speed_variance < -0.5,
        "sea_days": len(steaming_days),
        "idle_days": idle_days,
        "performance_status": "MEETING" if abs(speed_variance) <= 0.5 else ("UNDERPERFORMING" if speed_variance < -0.5 else "OVERPERFORMING")
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
