# JobPilot — AI-Assisted Job Application Automation Platform

> **Current Phase**: **Phase 4 — Job Source Architecture & Job Discovery Foundation** (Completed)  
> *Note: JobPilot is currently in Phase 4 (Job Discovery Foundation). Real LinkedIn/Indeed scraping, job matching, and application automation belong to future phases.*

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

## Resume Management API Endpoints (`/api/resumes`)

* `POST /api/resumes` — Upload resume document (PDF or DOCX, max 10MB)
* `GET /api/resumes` — List user's resumes
* `GET /api/resumes/{id}` — Fetch resume metadata
* `DELETE /api/resumes/{id}` — Delete resume metadata and physical storage file
* `GET /api/resumes/{id}/status` — Fetch processing status (`UPLOADED`, `PROCESSING`, `PROCESSED`, `FAILED`)
* `GET /api/resumes/{id}/parsed` — Fetch structured parsed section details
* `GET /api/resumes/{id}/quality` — Run 0-100 quality score analysis and suggestions
* `GET /api/resumes/{id}/consistency` — Compare resume against User Profile to detect mismatch findings
* `POST /api/resumes/{id}/reprocess` — Trigger re-running processing pipeline
* `POST /api/resumes/{id}/set-default` — Mark resume as preferred default
* `GET /api/resumes/{id}/download` — Securely stream resume file with ownership check

---

## Storage & Processing Pipeline Details

### Storage Configuration
- Configured via `RESUME_STORAGE_PATH=./storage/resumes` and `MAX_RESUME_FILE_SIZE_MB=10`.
- Physical files stored outside database using safe UUID filenames (e.g. `user_1_3f2b1a_filename.pdf`).
- Path traversal protection enforced on all read/write/delete operations.

### Resume Processing Pipeline
1. **Upload**: File validation (extension, MIME type, size) → Save to storage root.
2. **Text Extraction**: PDF (`pypdf`) or DOCX (`python-docx`). Detects empty / image-only scanned PDFs.
3. **Parsing**: Layer 1 regex section & keyword extraction (`DeterministicParser`) + Layer 2 `AIProvider` interface.
4. **Persistence**: Extracted skills, education, experiences, projects, certifications saved to database tables.
5. **Intelligence**: `ConsistencyService` compares against UserProfile; `QualityService` generates 0-100 quality score.

---

## Job Discovery API Endpoints (`/api/jobs`)

* `GET /api/jobs` — List jobs with filters (title, company, location, source, employment/workplace type, status) and pagination
* `GET /api/jobs/search` — Keyword search across job title, company_name, and description
* `GET /api/jobs/{id}` — Retrieve detailed job record
* `PATCH /api/jobs/{id}/status` — Update job status (`ACTIVE`, `EXPIRED`, `CLOSED`, `SKIPPED`, etc.)
* `GET /api/jobs/sources` — List registered job sources & configuration state
* `GET /api/jobs/sources/{source_name}` — Get specific source metadata & health
* `POST /api/jobs/sources/{source_name}/enable` — Enable target job source
* `POST /api/jobs/sources/{source_name}/disable` — Disable target job source
* `POST /api/jobs/discover` — Trigger job discovery across all enabled sources
* `POST /api/jobs/discover/{source_name}` — Trigger job discovery for a specific source adapter
* `GET /api/jobs/stats` — Retrieve overall job catalog and source metrics
* `GET /api/jobs/discovery-runs` — Retrieve historical discovery execution audit logs

---

## Job Discovery & Source Adapter Architecture

### 1. Adapter Interface (`JobSourceAdapter`)
All job sources implement a unified, platform-independent interface:
- `source_name()`, `display_name()`, `source_type()`
- `discover_jobs(limit, page)`, `get_job_details(external_id)`, `health_check()`
- Compliance metadata (`supported_access_method`, `requires_authentication`, `requires_human_interaction`, `automation_allowed`, `notes`).

### 2. Adapter Implementations & Limitations
- **`MockJobSourceAdapter` (`mock`)**: Fully working discovery source reading 20 synthetic jobs from `tests/fixtures/jobs.json`.
- **`LinkedInJobSourceAdapter` (`linkedin`)**: Placeholder adapter (raises `NotImplementedError`). Real scraping/automation is NOT implemented in Phase 4.
- **`IndeedJobSourceAdapter` (`indeed`)**: Placeholder adapter (raises `NotImplementedError`).
- **`CompanyCareersJobSourceAdapter` (`company_careers`)**: Placeholder adapter (raises `NotImplementedError`).

> **Compliance Note**: Real LinkedIn/Indeed integrations are NOT implemented in this phase. The mock adapter is currently the sole active discovery source. Stealth browser anti-bot evasion, CAPTCHA bypassing, and credential scraping are strictly prohibited.




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
