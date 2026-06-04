"""
Vessel Performance & Voyage Optimization Tool
Flask Backend — Main Application
"""

import os
import re
import io
import logging
import sqlite3
from datetime import datetime
import openpyxl
import requests as req
from flask import Flask, jsonify, send_from_directory, request, g
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Security Configurations
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'greenvoyage-fallback-secret-key-change-in-production')

# Configure CORS origins based on environment variable
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
if allowed_origins == '*':
    CORS(app)
else:
    CORS(app, origins=allowed_origins.split(','))

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

def get_direction_label(val):
    if val is None or str(val).strip() in ["-", "N/A", ""]:
        return "—"
    val_str = str(val).strip()
    try:
        num = float(val_str)
        mapping = {
            1.0: "N", 2.0: "NNE", 3.0: "NE", 4.0: "ENE",
            5.0: "E", 6.0: "ESE", 7.0: "SE", 8.0: "SSE",
            9.0: "S", 10.0: "SSW", 11.0: "SW", 12.0: "WSW",
            13.0: "W", 14.0: "WNW", 15.0: "NW", 16.0: "NNW"
        }
        return mapping.get(num, val_str)
    except:
        return val_str

def db_get_vessel_info():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, tech_manager, voyage, cargo, imo, period, delivery FROM vessel_info WHERE id = 1")
    row = cursor.fetchone()
    if row:
        return dict(row)
    return VESSEL_INFO

def db_get_noon_reports():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM noon_report ORDER BY date ASC")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def init_db():
    logger.info("Initializing database...")
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vessel_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT,
                tech_manager TEXT,
                voyage TEXT,
                cargo TEXT,
                imo TEXT,
                period TEXT,
                delivery TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS noon_report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                lat REAL,
                lon REAL,
                status TEXT,
                operation TEXT,
                condition TEXT,
                steaming_hrs REAL,
                distance_sailed REAL,
                speed_actual REAL,
                speed_warranted REAL,
                rpm INTEGER,
                slip_pct REAL,
                wind_dir TEXT,
                wind_speed REAL,
                wind_beaufort INTEGER,
                wave_height REAL,
                swell_dir TEXT,
                swell_height REAL,
                current_dir TEXT,
                current_speed REAL,
                fuel_vlsfo_rob REAL,
                fuel_lsmgo_rob REAL,
                fuel_consumed_me REAL,
                fuel_consumed_ae REAL,
                fuel_consumed_boiler REAL,
                fuel_consumed_me_mgo REAL,
                fuel_consumed_ae_mgo REAL,
                fuel_consumed_boiler_mgo REAL,
                fw_consumed REAL,
                fw_rob REAL,
                remarks TEXT
            )
        ''')
        conn.commit()

        # Seed data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM vessel_info")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding vessel_info table...")
            cursor.execute('''
                INSERT INTO vessel_info (id, name, tech_manager, voyage, cargo, imo, period, delivery)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                _seed_vessel["name"],
                _seed_vessel["tech_manager"],
                _seed_vessel["voyage"],
                _seed_vessel["cargo"],
                _seed_vessel["imo"],
                _seed_vessel["period"],
                _seed_vessel["delivery"]
            ))
            
        cursor.execute("SELECT COUNT(*) FROM noon_report")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding noon_report table...")
            for r in _seed_reports:
                cursor.execute('''
                    INSERT INTO noon_report (
                        date, lat, lon, status, operation, condition, steaming_hrs, distance_sailed,
                        speed_actual, speed_warranted, rpm, slip_pct, wind_dir, wind_speed, wind_beaufort,
                        wave_height, swell_dir, swell_height, current_dir, current_speed, fuel_vlsfo_rob,
                        fuel_lsmgo_rob, fuel_consumed_me, fuel_consumed_ae, fuel_consumed_boiler,
                        fuel_consumed_me_mgo, fuel_consumed_ae_mgo, fuel_consumed_boiler_mgo,
                        fw_consumed, fw_rob, remarks
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    r["date"], r["lat"], r["lon"], r["status"], r["operation"], r["condition"], r["steaming_hrs"],
                    r["distance_sailed"], r["speed_actual"], r["speed_warranted"], r["rpm"], r["slip_pct"],
                    r["wind_dir"], r["wind_speed"], r["wind_beaufort"], r["wave_height"], r["swell_dir"],
                    r["swell_height"], r["current_dir"], r["current_speed"], r["fuel_vlsfo_rob"], r["fuel_lsmgo_rob"],
                    r["fuel_consumed_me"], r["fuel_consumed_ae"], r["fuel_consumed_boiler"], r["fuel_consumed_me_mgo"],
                    r["fuel_consumed_ae_mgo"], r["fuel_consumed_boiler_mgo"], r["fw_consumed"], r["fw_rob"], r["remarks"]
                ))
            conn.commit()

# Database file path configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///greenvoyage.db')
if DATABASE_URL.startswith('sqlite:///'):
    DATABASE_PATH = DATABASE_URL.replace('sqlite:///', '')
else:
    DATABASE_PATH = 'greenvoyage.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def load_data_from_pdf_text(filepath):
    if not os.path.exists(filepath):
        return None, None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None, None
        
    pages = content.split("=== Page")
    if len(pages) <= 1:
        return None, None
        
    # 1. Parse Vessel Name from Page 1
    vessel_name = "XYZ"
    p1 = pages[1]
    for line in p1.split("\n"):
        if "V E S S E L  P E R F O R M A N C E  R E P O R T" in line:
            continue
        cleaned = line.strip()
        if cleaned:
            if "M/V" in cleaned or "M/T" in cleaned or "XYZ" in cleaned:
                vessel_name = cleaned.replace("M/V", "").replace("M/T", "").strip()
                break
                
    # 2. Parse Page 6 for steaming hours, operation, and remarks
    p6 = pages[6] if len(pages) > 6 else ""
    date_regex = re.compile(r"^\s*([0-3][0-9]-[A-Za-z]{3})")
    
    page6_data = {}
    for line in p6.split("\n"):
        line = line.strip()
        if not line or "TOTAL" in line.upper():
            continue
        m = date_regex.match(line)
        if m:
            date_label = m.group(1)
            tokens = re.split(r"\s+", line)
            page6_data[date_label] = {
                "operation": tokens[1],
                "steaming_hrs": float(tokens[2]) if tokens[2] not in ["-", "N/A"] else 0.0,
                "remarks": " ".join(tokens[11:]) if len(tokens) > 11 else ""
            }
            
    # 3. Parse Page 3 for wind, waves, currents
    p3 = pages[3] if len(pages) > 3 else ""
    page3_data = {}
    for line in p3.split("\n"):
        line = line.strip()
        if not line or "TOTAL" in line.upper():
            continue
        m = date_regex.match(line)
        if m:
            date_label = m.group(1)
            tokens = re.split(r"\s+", line)
            try:
                page3_data[date_label] = {
                    "current_speed": float(tokens[-1]) if tokens[-1] not in ["-", "N/A", ""] else 0.0,
                    "current_dir": get_direction_label(tokens[-2]),
                    "swell_height": float(tokens[-3]) if tokens[-3] not in ["-", "N/A", ""] else 0.0,
                    "swell_dir": get_direction_label(tokens[-4]),
                    "wave_height": float(tokens[-5]) if tokens[-5] not in ["-", "N/A", ""] else 0.0,
                    "wind_beaufort": int(tokens[-6]) if tokens[-6] not in ["-", "N/A", ""] else 0,
                    "wind_speed": float(tokens[-7]) if tokens[-7] not in ["-", "N/A", ""] else 0.0,
                    "wind_dir": get_direction_label(tokens[-8])
                }
            except:
                pass
                
    # 4. Parse Page 4 for bunkers and final records
    p4 = pages[4] if len(pages) > 4 else ""
    reports = []
    
    current_date = None
    for line in p4.split("\n"):
        line = line.strip()
        if not line or "TOTAL" in line.upper():
            continue
            
        if re.match(r"^\d+-[A-Za-z]{3}$", line):
            current_date = line
            continue
            
        m = date_regex.match(line)
        tokens = re.split(r"\s+", line)
        
        # If the line starts with time e.g. "12:00"
        if re.match(r"^\d{2}:\d{2}", tokens[0]):
            if current_date:
                date_label = current_date
                time_label = tokens[0]
                is_starts_with_date = False
            else:
                continue
        elif m:
            date_label = m.group(1)
            time_label = "12:00" # default
            is_starts_with_date = True
        else:
            continue
            
        # Ignore "00:01" Delivery row
        if time_label == "00:01":
            continue
            
        # Extract lat/lon tokens
        idx_at = -1
        for idx in range(len(tokens)):
            if tokens[idx] == "At":
                idx_at = idx
                break
        
        lat_val = 0.0
        lon_val = 0.0
        if idx_at != -1:
            lat_tokens = []
            lon_tokens = []
            
            if is_starts_with_date:
                if len(tokens) > 1 and re.match(r"^\d{2}:\d{2}", tokens[1]):
                    coord_tokens = tokens[2:idx_at]
                else:
                    coord_tokens = tokens[1:idx_at]
            else:
                coord_tokens = tokens[1:idx_at]
            
            split_idx = -1
            for k in range(len(coord_tokens)):
                if "N" in coord_tokens[k] or "S" in coord_tokens[k]:
                    split_idx = k
                    break
            if split_idx != -1:
                lat_tokens = coord_tokens[:split_idx+1]
                lon_tokens = coord_tokens[split_idx+1:]
                
            def parse_tokens_coord(t_list):
                if not t_list:
                    return 0.0
                joined = " ".join(t_list).upper()
                m_num = re.findall(r"([0-9\.]+)", joined)
                if len(m_num) >= 2:
                    return float(m_num[0]) + float(m_num[1]) / 60.0
                elif len(m_num) == 1:
                    return float(m_num[0])
                return 0.0
                
            lat_val = parse_tokens_coord(lat_tokens)
            lon_val = parse_tokens_coord(lon_tokens)
            
        def get_num(idx, default=0.0):
            try:
                val = tokens[idx]
                if val in ["-", "N/A", ""]:
                    return default
                return float(val)
            except:
                return default
                
        dist_val = get_num(-19, 0.0)
        speed_val = get_num(-18, 0.0)
        rpm_val = int(get_num(-16, 0.0))
        slip_val = get_num(-15, 0.0)
        
        lsfo_rob = get_num(-14, 0.0)
        mgo_rob = get_num(-13, 0.0)
        
        me_lsfo = get_num(-9, 0.0)
        ae_lsfo = get_num(-8, 0.0)
        boiler_lsfo = get_num(-7, 0.0)
        
        me_mgo = get_num(-6, 0.0)
        ae_mgo = get_num(-5, 0.0)
        boiler_mgo = get_num(-4, 0.0)
        
        fw_cons = get_num(-3, 0.0)
        fw_rob = get_num(-1, 0.0)
        
        try:
            date_dt = datetime.strptime(f"{date_label}-2026", "%d-%b-%Y")
            date_str = date_dt.strftime("%Y-%m-%d")
        except:
            date_str = date_label
            
        p6_info = page6_data.get(date_label, {"operation": "Idle", "steaming_hrs": 0.0, "remarks": ""})
        p3_info = page3_data.get(date_label, {
            "current_speed": 0.0, "current_dir": "—", "swell_height": 0.0, "swell_dir": "—",
            "wave_height": 0.0, "wind_beaufort": 0, "wind_speed": 0.0, "wind_dir": "—"
        })
        
        reports.append({
            "date": date_str,
            "lat": round(lat_val, 3),
            "lon": round(lon_val, 3),
            "status": "At Sea" if dist_val > 0 else "At Port",
            "operation": p6_info["operation"],
            "condition": "Ballast",
            "steaming_hrs": p6_info["steaming_hrs"],
            "distance_sailed": dist_val,
            "speed_actual": speed_val,
            "speed_warranted": 12.5,
            "rpm": rpm_val,
            "slip_pct": slip_val,
            "wind_dir": p3_info["wind_dir"],
            "wind_speed": p3_info["wind_speed"],
            "wind_beaufort": p3_info["wind_beaufort"],
            "wave_height": p3_info["wave_height"],
            "swell_dir": p3_info["swell_dir"],
            "swell_height": p3_info["swell_height"],
            "current_dir": p3_info["current_dir"],
            "current_speed": p3_info["current_speed"],
            "fuel_vlsfo_rob": lsfo_rob,
            "fuel_lsmgo_rob": mgo_rob,
            "fuel_consumed_me": me_lsfo,
            "fuel_consumed_ae": ae_lsfo,
            "fuel_consumed_boiler": boiler_lsfo,
            "fuel_consumed_me_mgo": me_mgo,
            "fuel_consumed_ae_mgo": ae_mgo,
            "fuel_consumed_boiler_mgo": boiler_mgo,
            "fw_consumed": fw_cons,
            "fw_rob": fw_rob,
            "remarks": p6_info["remarks"]
        })
        
    return vessel_name, reports

# Setup seed values prior to seeding (allowing pdf_text load to override if file exists)
_seed_vessel = dict(VESSEL_INFO)
_seed_reports = list(NOON_REPORTS)

# Try to load initial data from pdf_text.txt
try:
    _txt_path = os.path.join(os.path.dirname(__file__), 'pdf_text.txt')
    if os.path.exists(_txt_path):
        _parsed_vessel, _parsed_reports = load_data_from_pdf_text(_txt_path)
        if _parsed_vessel and _parsed_reports:
            _seed_vessel["name"] = _parsed_vessel
            _seed_reports = _parsed_reports
            logger.info("Loaded seed data from pdf_text.txt")
except Exception as _e:
    logger.warning(f"Failed to load start data from pdf_text.txt: {_e}")

# Initialize and seed database
init_db()


# Warranted performance (Charter Party)
CP_WARRANTED = {
    "speed_knots": 12.5,
    "fuel_consumption_mt_day": 23.5,  # VLSFO in ballast condition (Eco speed 12.5)
    "conditions": "Beaufort ≤ 4, Douglas Sea State ≤ 3",
    "idle_warranted": 5.5
}

def parse_excel_noon_reports(file_source):
    wb = openpyxl.load_workbook(file_source, data_only=True)
    
    sheet = None
    for name in wb.sheetnames:
        if "GUIDELINE" in name.upper():
            continue
        sheet = wb[name]
        break
    if not sheet:
        sheet = wb.active
        
    reports = []
    row_mapping = {}
    for r in range(1, 100):
        val2 = sheet.cell(r, 2).value
        val1 = sheet.cell(r, 1).value
        header = str(val2 or val1 or "").strip().upper()
        if header:
            row_mapping[header] = r

    def get_row(header_text, default_row):
        header_text = header_text.upper()
        for k, v in row_mapping.items():
            if header_text in k:
                return v
        return default_row

    r_date = get_row("UTC DATE", 10)
    r_lat = get_row("LATITUDE", 12)
    r_lon = get_row("LONGITUDE", 13)
    r_cond = get_row("VESSEL CONDITION", 14)
    r_dist = get_row("ENGINE DISTANCE 24 HRS", 23)
    if "ENGINE DISTANCE 24 HRS" not in row_mapping:
        r_dist = get_row("DISTANCE SAILED", 22)
    r_speed = get_row("SPEED LAST 24 HRS", 28)
    r_rpm = get_row("MAIN ENGINE RPM", 30)
    r_slip = get_row("AVERAGE SLIP", 31)
    r_wind_spd = get_row("WIND SPEED", 34)
    r_wind_dir = get_row("WIND DIRECTION", 35)
    r_current_dir = get_row("CURRENT DIRECTION", 36)
    r_bf = get_row("BUEFORT SCALE", 37)
    r_me_lsfo = get_row("ME LSFO CONSUMPTION", 45)
    r_ae_lsfo = get_row("AE LSFO CONSUMPTION", 48)
    r_boiler_lsfo = get_row("BOILER LSFO CONSUMPTION", 51)
    r_me_mgo = get_row("ME MGO CONSUMPTION", 46)
    r_ae_mgo = get_row("AE MGO CONSUMPTION", 49)
    r_boiler_mgo = get_row("BOILER MGO CONSUMPTION", 52)
    r_lsfo_rob = get_row("ROB LSFO", 60)
    r_mgo_rob = get_row("ROB MGO", 61)
    r_fw_cons = get_row("FRESH WATER CONSUMED", 63)
    r_fw_rob = get_row("FRESH WATER ROB", 65)
    r_remarks = get_row("OTHER REMARKS IF ANY", 69)

    col = 3
    while True:
        date_val = sheet.cell(r_date, col).value
        if date_val is None:
            break
            
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val).strip()
            
        if not date_str or date_str in ["-", "N/A"]:
            break
            
        def parse_coord(coord_str, is_lat=True):
            if coord_str is None:
                return 0.0
            coord_str = str(coord_str).strip().upper()
            if coord_str in ["-", "N/A", ""]:
                return 0.0
            m = re.findall(r"([0-9\.]+)", coord_str)
            if len(m) >= 2:
                deg = float(m[0])
                mins = float(m[1])
                val = deg + mins / 60.0
            elif len(m) == 1:
                val = float(m[0])
            else:
                val = 0.0
            return val

        lat_val = parse_coord(sheet.cell(r_lat, col).value, is_lat=True)
        lon_val = parse_coord(sheet.cell(r_lon, col).value, is_lat=False)
        
        def get_num(row, default=0.0):
            val = sheet.cell(row, col).value
            if val is None or str(val).strip() in ["-", "N/A", "NIL", ""]:
                return default
            try:
                return float(val)
            except:
                return default

        dist_val = get_num(r_dist, 0.0)
        speed_val = get_num(r_speed, 0.0)
        rpm_val = int(get_num(r_rpm, 0.0))
        slip_val = get_num(r_slip, 0.0)
        
        steaming_hrs = round(dist_val / speed_val, 1) if speed_val > 0 else 0.0
        
        cond = str(sheet.cell(r_cond, col).value or "Ballast").strip()
        status = "At Sea" if dist_val > 0 else "At Port"
        
        remarks_val = str(sheet.cell(r_remarks, col).value or "").strip()
        if dist_val > 0:
            operation = "Manoeuvring" if "MANOEUVRING" in remarks_val.upper() else "Steaming"
        else:
            operation = "Idle"
            
        wind_spd = get_num(r_wind_spd, 0.0)
        bf = int(get_num(r_bf, 0.0))

        wind_dir = get_direction_label(sheet.cell(r_wind_dir, col).value)
        current_dir = get_direction_label(sheet.cell(r_current_dir, col).value)
        
        current_spd_row = get_row("CURRENT SPEED", 0)
        if current_spd_row > 0:
            current_spd = get_num(current_spd_row, 0.0)
        else:
            current_spd = 0.5 if current_dir != "—" else 0.0
        
        me_lsfo = get_num(r_me_lsfo, 0.0)
        ae_lsfo = get_num(r_ae_lsfo, 0.0)
        boiler_lsfo = get_num(r_boiler_lsfo, 0.0)
        me_mgo = get_num(r_me_mgo, 0.0)
        ae_mgo = get_num(r_ae_mgo, 0.0)
        boiler_mgo = get_num(r_boiler_mgo, 0.0)
        
        lsfo_rob = get_num(r_lsfo_rob, 950.0)
        mgo_rob = get_num(r_mgo_rob, 245.0)
        
        fw_cons = get_num(r_fw_cons, 5.0)
        fw_rob = get_num(r_fw_rob, 200.0)
        
        reports.append({
            "date": date_str,
            "lat": round(lat_val, 3),
            "lon": round(lon_val, 3),
            "status": status,
            "operation": operation,
            "condition": "Ballast" if "BALLAST" in cond.upper() else "Laden",
            "steaming_hrs": steaming_hrs,
            "distance_sailed": dist_val,
            "speed_actual": speed_val,
            "speed_warranted": 12.5,
            "rpm": rpm_val,
            "slip_pct": slip_val,
            "wind_dir": wind_dir,
            "wind_speed": wind_spd,
            "wind_beaufort": bf,
            "wave_height": 0.5 if bf > 1 else 0.0,
            "swell_dir": wind_dir,
            "swell_height": 0.4 if bf > 1 else 0.0,
            "current_dir": current_dir,
            "current_speed": current_spd,
            "fuel_vlsfo_rob": lsfo_rob,
            "fuel_lsmgo_rob": mgo_rob,
            "fuel_consumed_me": me_lsfo,
            "fuel_consumed_ae": ae_lsfo,
            "fuel_consumed_boiler": boiler_lsfo,
            "fuel_consumed_me_mgo": me_mgo,
            "fuel_consumed_ae_mgo": ae_mgo,
            "fuel_consumed_boiler_mgo": boiler_mgo,
            "fw_consumed": fw_cons,
            "fw_rob": fw_rob,
            "remarks": remarks_val
        })
        col += 1
        
    return reports

# ─────────────────────────────────────────────
# PERFORMANCE CALCULATIONS
# ─────────────────────────────────────────────

def calculate_performance_metrics(reports=None):
    if reports is None:
        reports = db_get_noon_reports()
        
    # Only calculate average speed for days with actual movement
    steaming_days = [r for r in reports if r["distance_sailed"] > 0]
    total_distance = sum(r["distance_sailed"] for r in reports)
    
    avg_speed = sum(r["speed_actual"] for r in steaming_days) / len(steaming_days) if steaming_days else 10.35
    
    total_lsfo_consumed = sum(r["fuel_consumed_me"] + r["fuel_consumed_ae"] + r["fuel_consumed_boiler"] for r in reports)
    total_mgo_consumed = sum(r["fuel_consumed_me_mgo"] + r["fuel_consumed_ae_mgo"] + r["fuel_consumed_boiler_mgo"] for r in reports)
    
    # Idle/anchorage days: status == "At Port" and steaming_hrs == 0
    idle_days = len([r for r in reports if r["status"] == "At Port" and r["steaming_hrs"] == 0])

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
    return jsonify(db_get_vessel_info())

@app.route('/api/noon-reports')
def noon_reports():
    return jsonify(db_get_noon_reports())

@app.route('/api/performance')
def performance():
    vessel = db_get_vessel_info()
    reports = db_get_noon_reports()
    metrics = calculate_performance_metrics(reports)
    return jsonify({
        "vessel": vessel,
        "metrics": metrics,
        "cp_warranted": CP_WARRANTED,
        "daily_data": reports
    })

@app.route('/api/track')
def vessel_track():
    """Return lat/lon positions for map plotting."""
    reports = db_get_noon_reports()
    track = [
        {
            "date": r["date"],
            "lat": r["lat"],
            "lon": r["lon"],
            "status": r["status"],
            "speed": r["speed_actual"],
            "beaufort": r["wind_beaufort"]
        }
        for r in reports
    ]
    return jsonify(track)

@app.route('/api/weather-route')
def weather_route():
    """
    Fetch marine weather from Open-Meteo along the Singapore → Sungai Linggi route.
    Uses a few waypoints along the route.
    """
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


@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and file.filename.endswith('.xlsx'):
        try:
            file_bytes = io.BytesIO(file.read())
            parsed_reports = parse_excel_noon_reports(file_bytes)
            
            if not parsed_reports:
                return jsonify({"error": "No valid records found in the spreadsheet. Make sure you upload a valid Noon position report sheet."}), 400
                
            db = get_db()
            cursor = db.cursor()
            try:
                # 1. Clear old reports
                cursor.execute("DELETE FROM noon_report")
                
                # 2. Insert new reports
                for r in parsed_reports:
                    cursor.execute('''
                        INSERT INTO noon_report (
                            date, lat, lon, status, operation, condition, steaming_hrs, distance_sailed,
                            speed_actual, speed_warranted, rpm, slip_pct, wind_dir, wind_speed, wind_beaufort,
                            wave_height, swell_dir, swell_height, current_dir, current_speed, fuel_vlsfo_rob,
                            fuel_lsmgo_rob, fuel_consumed_me, fuel_consumed_ae, fuel_consumed_boiler,
                            fuel_consumed_me_mgo, fuel_consumed_ae_mgo, fuel_consumed_boiler_mgo,
                            fw_consumed, fw_rob, remarks
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    ''', (
                        r["date"], r["lat"], r["lon"], r["status"], r["operation"], r["condition"], r["steaming_hrs"],
                        r["distance_sailed"], r["speed_actual"], r["speed_warranted"], r["rpm"], r["slip_pct"],
                        r["wind_dir"], r["wind_speed"], r["wind_beaufort"], r["wave_height"], r["swell_dir"],
                        r["swell_height"], r["current_dir"], r["current_speed"], r["fuel_vlsfo_rob"], r["fuel_lsmgo_rob"],
                        r["fuel_consumed_me"], r["fuel_consumed_ae"], r["fuel_consumed_boiler"], r["fuel_consumed_me_mgo"],
                        r["fuel_consumed_ae_mgo"], r["fuel_consumed_boiler_mgo"], r["fw_consumed"], r["fw_rob"], r["remarks"]
                    ))
                
                # 3. Extract Tech Manager and Vessel Name from the sheet if available
                vessel_updates = {}
                try:
                    file_bytes.seek(0)
                    wb = openpyxl.load_workbook(file_bytes, data_only=True)
                    sheet = None
                    for name in wb.sheetnames:
                        if "GUIDELINE" in name.upper():
                            continue
                        sheet = wb[name]
                        break
                    if sheet:
                        for r_idx in range(1, 20):
                            val1 = str(sheet.cell(r_idx, 1).value or "").strip().upper()
                            if "VESSEL" in val1:
                                val2 = sheet.cell(r_idx, 2).value
                                if val2:
                                    vessel_updates["name"] = str(val2).strip()
                            elif "TECH MANAGER" in val1:
                                val2 = sheet.cell(r_idx, 2).value
                                if val2:
                                    vessel_updates["tech_manager"] = str(val2).strip()
                except Exception as e:
                    logger.warning(f"Failed to extract vessel info from uploaded sheet: {e}")

                if vessel_updates:
                    for key, val in vessel_updates.items():
                        cursor.execute(f"UPDATE vessel_info SET {key} = ? WHERE id = 1", (val,))
                
                db.commit()
            except Exception as db_e:
                db.rollback()
                raise db_e
                
            return jsonify({
                "message": "File parsed successfully",
                "count": len(parsed_reports),
                "vessel": db_get_vessel_info()
            })
            
        except Exception as e:
            logger.exception("Failed to parse or save uploaded Excel file")
            return jsonify({"error": f"Failed to parse Excel file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .xlsx files are supported."}), 400


if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    try:
        port = int(os.getenv('PORT', 5000))
    except ValueError:
        port = 5000
    
    flask_env = os.getenv('FLASK_ENV', 'production')
    
    logger.info("Vessel Performance & Voyage Optimization Tool starting...")
    if flask_env == 'production':
        logger.info(f"Starting Waitress production server at http://{host}:{port}")
        from waitress import serve
        serve(app, host=host, port=port)
    else:
        logger.info(f"Starting Flask development server at http://{host}:{port} (debug=True)")
        app.run(host=host, port=port, debug=True)
