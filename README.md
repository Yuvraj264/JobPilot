# JobPilot — AI-Assisted Job Application Automation Platform

> **Current Phase**: **Phase 2 — User Profile & Preference Engine** (Completed)  
> *Note: JobPilot is currently in Phase 2 (Profile Engine). Job discovery, resume parsing/tailoring, matching, and application automation belong to future phases.*

---

## About JobPilot

JobPilot is an open, modular platform designed to assist job seekers by automating repetitive aspects of job discovery, fit evaluation, and application form filling while maintaining strict truthfulness and requiring human approval before submission.

### Long-Term Goal
- Discover jobs across multiple permitted platforms via an adapter-based architecture.
- Normalize job descriptions and evaluate them against user profiles.
- Tailor application materials using verifiable information from the user's profile.
- Automate form entry using browser automation.
- Generate truthful screening question answers.
- Pause for human approval before final submission.
- Track applications across all stages.

---

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic, SQLAlchemy 2.0, PostgreSQL, Alembic
- **Browser Automation**: Playwright for Python
- **Frontend**: React (Vite) minimal status placeholder
- **Infrastructure**: Docker Compose, `.env` configuration

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Docker & Docker Compose
- Virtualenv (`python3 -m venv .venv`)

---

### 1. Environment Setup
Copy `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```

---

### 2. Start PostgreSQL Database
Start the database service via Docker Compose:
```bash
docker-compose up -d db
```

---

### 3. Setup & Start Backend
Create virtual environment, install dependencies, and run the FastAPI app:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run backend development server
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at `http://localhost:8000`.  
Swagger API Docs available at `http://localhost:8000/docs`.

---

### 4. Run Database Migrations
Apply Alembic migrations to PostgreSQL:
```bash
cd backend
PYTHONPATH=. alembic upgrade head
```

---

### 5. Seed Development Sample Profile
Generate realistic fake development test data:
```bash
curl -X POST http://localhost:8000/api/profile/seed
```

---

### 6. Install Playwright & Verify Browser Launch
Install Playwright Chromium browser binaries:
```bash
playwright install chromium
```
Verify browser launch capability:
```bash
python3 browser-agent/browser.py
```

---

### 7. Setup & Start Frontend
In a new terminal tab:
```bash
cd frontend
npm install
npm run dev
```
Frontend interface available at `http://localhost:5173`.

---

### 8. Run Automated Tests
Run pytest test suite:
```bash
# Make sure virtualenv is activated
PYTHONPATH=backend:browser-agent pytest tests/
```

---

## User Profile API Endpoints (`/api/profile`)

* `GET /api/profile` — Fetch full user profile
* `POST /api/profile` — Create user profile
* `PUT /api/profile` — Update basic & professional information
* `DELETE /api/profile` — Delete user profile
* `GET /api/profile/summary` — Compact structured profile representation for AI/matching engines
* `GET /api/profile/completeness` — Deterministic completeness % score & missing section identifiers
* `GET/POST/PUT/DELETE /api/profile/education` — Education sub-resource CRUD
* `GET/POST/PUT/DELETE /api/profile/skills` — Skills sub-resource CRUD
* `GET/POST/PUT/DELETE /api/profile/projects` — Projects sub-resource CRUD
* `GET/POST/PUT/DELETE /api/profile/certifications` — Certifications sub-resource CRUD
* `GET/PUT /api/profile/preferences/job` — Job preferences update
* `GET/PUT /api/profile/preferences/application` — Application automation preferences update
* `POST /api/profile/seed` — Development fake data seeder


---

## Project Structure

```
jobpilot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── automation/
│   │   ├── database/
│   │   │   └── connection.py
│   │   ├── models/
│   │   ├── config.py
│   │   └── main.py
│   └── alembic/
│   └── requirements.txt
├── browser-agent/
│   ├── browser.py
│   ├── inspector.py
│   ├── actions.py
│   └── agent.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── tests/
├── docs/
├── flow.md
├── context.md
├── README.md
├── .env.example
├── .gitignore
└── docker-compose.yml
```
