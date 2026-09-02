# PMPC Data Logger System

The **PMPC Data Logger System** (Production Management System) is a comprehensive web-based application designed for Panasonic Manufacturing Philippines Corporation. It provides real-time tracking, quality control, scheduling, and data logging for production lines.

## Features

- **Dashboard & Scoreboards:** Real-time visibility into production performance.
- **Station Monitoring:** Track assemblies and verification results across multiple inspection points:
  - Compressor Registration (CRS)
  - Gas Management System (GMS)
  - Air Tight Test (ATT)
  - Safety Parts Monitoring (SPAMS)
  - Control Board & PCB (CBPCB)
  - Inspections (Running, Vibration, Final)
- **Production Management:** Maintain work schedules, Bills of Materials (BOM), and production line configurations.
- **Quality Control (QC):** Finished goods tracking, defect management, and repair station logs.
- **System Administration:** User management, global configuration, and full audit trails.

## Tech Stack

### Backend
- **Python / Flask:** Web framework handling routing and API endpoints.
- **SQLAlchemy:** ORM for database interaction.
- **MySQL (8.x):** Primary relational database for PLC data, configurations, and logs.
- **Redis:** In-memory data structure store used for secure, fast session management.

### Frontend
- **HTML5 & CSS3:** Custom, modern styling leveraging CSS variables (no external dependencies required to run offline).
- **Vanilla JavaScript:** Responsive, lightweight client-side interaction with dynamically updating data tables, unified sorting, and loading states.
- **Chart.js / DataViz:** Used for dashboard metrics and scoreboards.

## Prerequisites

- Python 3.9+
- MySQL Server 8.x
- Redis Server (Running locally or via Docker)

## Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd "Panasonic Web"
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory based on the configuration required in `config.py`:
   ```env
   SECRET_KEY=your_secure_secret_key_here
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=plcdata
   REDIS_HOST=127.0.0.1
   REDIS_PORT=6379
   ```
   *(Generate a secure secret key by running: `python -c "import secrets; print(secrets.token_hex(32))"`)*

5. **Database Initialization**
   Apply database migrations to set up the MySQL schema:
   ```bash
   flask db upgrade
   ```

## Running the Application

Start the Flask development server:
```bash
flask run --host=0.0.0.0 --port=5000
```
Then navigate to `http://localhost:5000` in your web browser.

## Security & Architecture

- **100% Offline Capable:** The frontend is built without relying on CDNs or external web fonts, ensuring the system functions flawlessly in isolated factory network environments.
- **Authentication:** Role-based access control and session management via Redis.

---
*Developed for Panasonic Manufacturing Philippines Corporation (PMPC).*
