# GreenVoyage 🚢🍃

GreenVoyage is a premium, production-ready Vessel Performance & Voyage Optimization web platform. It enables managers and operators to track steaming performance, optimize voyages using live marine weather datasets, evaluate compliance against Charter Party (CP) agreements, and export official performance reports.

---

## 🌟 Key Features

* **Vessel Performance Dashboard:** Real-time KPI monitors displaying speed variance, daily fuel consumption drawdown rates, overall performance status, and off-hire claim risks.
* **Voyage Optimizer & Route Planner:** Interactive route comparisons between direct and weather-optimized routes, with projected fuel, cost, and $CO_2$ emission savings.
* **Charter Party Claim Analytics:** Automated compliance analysis matching noon reports against warranted speed and consumption parameters (Beaufort wind scale $\le$ 4, Sea State $\le$ 3 limits).
* **Official 10-Page Voyage Report:** Professional multi-page report structure featuring comprehensive narratives, fuel ROB drawdowns, visual charts, system efficiency statistics, and detailed maps.
* **Atomic Excel Position Importer:** Dynamic parser uploading noon position sheets, parsing records using `openpyxl`, and writing transactionally to the database.

---

## 🛠️ Technology Stack

* **Backend Engine:**
  * [Flask 3.0.3](https://flask.palletsprojects.com/) — Application Framework
  * SQLite3 (Persistent Store) — Thread-safe, transaction-supported local database
  * [Waitress 3.0.0](https://docs.pylonsproject.org/projects/waitress/en/latest/) — Production WSGI HTTP server
  * [openpyxl 3.1.2](https://openpyxl.readthedocs.io/) — Excel Sheet Processing
  * [python-dotenv 1.0.1](https://pypi.org/project/python-dotenv/) — Environment Variables Loader
* **Frontend Interface:**
  * Vanilla HTML5 & CSS3 — Modern styling with custom responsive grids and dark glassmorphic styles
  * Javascript (ES6+) — Dynamic state rendering and API synchronization
  * [Chart.js](https://www.chartjs.org/) — Data visualization (consumption drawdowns, speed variances)
  * [Leaflet Map API](https://leafletjs.com/) — Geographical path visualizations and waypoint marker plotting

---

## ⚙️ Environment Configuration

Copy the template environment file to define your configuration:
```bash
copy .env.example .env
```

Configuration variables in `.env`:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `FLASK_ENV` | Mode of operation (`production` or `development`). | `production` |
| `HOST` | Bind address for the server. | `127.0.0.1` |
| `PORT` | Bind port for incoming requests. | `5000` |
| `SECRET_KEY` | Key used for cryptographically signing session cookies. | `greenvoyage-secure-dev-key-change-me-in-production` |
| `ALLOWED_ORIGINS` | Comma-separated list of permitted CORS domains. Use `*` to allow all. | `*` |
| `DATABASE_URL` | SQLite connection URL path. | `sqlite:///greenvoyage.db` |

---

## 🚀 Setup & Execution

### Prerequisites
* Python 3.8 or higher.

### 1. Install Dependencies
Run the following command to download and configure required modules:
```bash
pip install -r requirements.txt
```

### 2. Database Initialization
The application will **automatically create and seed** the database (`greenvoyage.db`) on its initial startup using historical default noon reports, or you can run the parsing test suite to initialize it.

### 3. Run the Application
Start the application using the runner command:
```bash
python app.py
```
* **Production Mode (`FLASK_ENV=production`):** App will run securely using the Waitress WSGI server (default).
* **Development Mode (`FLASK_ENV=development`):** App will run in Flask debug mode with the hot-reloader active.

Once running, navigate to `http://localhost:5000` in your web browser.

---

## 🧪 Verification & Testing

Verify the Excel parser and seed the database using the test suite:
```bash
python test_parse.py
```
This script reads the sample Position report sheet under `PROMBLEM-STATEMENT/NOON REPORT- SAMPLE.xlsx` and validates database interactions.

---

## 📁 Directory Structure

```text
├── PROMBLEM-STATEMENT/   # Historical data, sample Excel sheets, and PDFs
├── static/
│   ├── css/
│   │   └── style.css     # Dark glassmorphic design sheets
│   └── js/
│       ├── api.js        # API service layer
│       ├── dashboard.js  # Main UI controller & Chart.js builders
│       └── map.js        # Leaflet map rendering module
├── app.py                # Main Flask Backend, SQLite controllers, and API routes
├── index.html            # Main SPA dashboard interface
├── requirements.txt      # Python package dependencies
├── .env                  # Local configuration settings (Ignored)
└── README.md             # Project documentation
```
