# JobPilot — AI-Assisted Job Application Automation Platform

> **Current Phase**: **Phase 6 — Mock Application Environment & Application Agent Foundation** (Completed)  
> *Note: JobPilot operates browser automation exclusively against the local mock environment (`/mock/apply/*`). Real job-platform automation is NOT implemented yet.*

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

---

## Job Matching API Endpoints (`/api/matching`)

* `POST /api/matching/job/{job_id}` — Evaluate a single job against current user profile
* `GET /api/matching/job/{job_id}` — Retrieve existing match evaluation result and structured explanation
* `GET /api/matching/jobs` — List evaluated job matches with filters (`recommendation`, `min_score`, `eligible_only`) and pagination
* `POST /api/matching/run` — Trigger batch matching run across active catalog jobs
* `GET /api/matching/runs` — Retrieve historical batch matching execution logs
* `GET /api/matching/runs/{id}` — Retrieve single match run details
* `GET /api/matching/stats` — Retrieve matching metrics (`jobs_evaluated`, `eligible`, `apply`, `review`, `skip`, `average_score`)
* `GET /api/matching/config` — Retrieve scoring weights and recommendation thresholds
* `PUT /api/matching/config` — Update scoring weights and recommendation thresholds

---

## Job Matching & Selection Architecture

### 1. Conceptual Evaluation Pipeline
```text
Normalized Job + Candidate Profile
               ↓
        EligibilityEngine
    (Hard Failure check -> SKIP)
               ↓
       Component Matchers
  (Skills, Role, Location, etc.)
               ↓
        ScoringEngine
 (Weighted Score & Confidence)
               ↓
      RecommendationEngine
    (APPLY / REVIEW / SKIP)
               ↓
     ExplanationGenerator
 (Human-readable Facts & Reasons)
```

### 2. Weighted Scoring & Threshold Defaults
- **Skills Match**: 35%
- **Role Similarity**: 20%
- **Experience Bounds**: 15%
- **Location Alignment**: 10%
- **Workplace Arrangement**: 5%
- **Employment Type**: 5%
- **Education Qualification**: 5%
- **Semantic Similarity**: 5%

**Recommendation Thresholds**:
- `APPLY`: Match Score &ge; 85% (or user's `minimum_job_match_score` preference) & Eligible
- `REVIEW`: Match Score 70% – 84% & Eligible
- `SKIP`: Match Score < 70% OR Hard Constraint Failure

> **Automation Boundary Note**: JobPilot evaluates match fit and generates transparent recommendations, but does **NOT** automatically submit applications in Phase 5.

---

## Application Agent API Endpoints (`/api/automation`)

* `POST /api/automation/run` — Start browser automation run against target job
* `GET /api/automation/runs` — List historical automation runs
* `GET /api/automation/runs/{id}` — Retrieve detailed run status and state machine timeline
* `POST /api/automation/runs/{id}/resume` — Resume a paused automation run
* `POST /api/automation/runs/{id}/pause` — Pause an active automation run
* `GET /api/automation/runs/{id}/actions` — Retrieve step-by-step action audit logs
* `GET /api/automation/runs/{id}/screenshots` — Retrieve captured step screenshot metadata

---

## Application Agent Architecture

```text
ApplicationAgent
       ↓
BrowserController (Playwright Chromium Wrapper)
       ↓
PageInspector (DOM Structured Element Extractor)
       ↓
FormAnalyzer (Deterministic Semantic Field Classification)
       ↓
ProfileFieldMapper (Profile & Resume Fact Mapping with Confidence)
       ↓
ApplicationActionPlanner (Validated Action Plan Generator)
       ↓
ApplicationActionExecutor (5-Tier Selector Priority Execution)
       ↓
Step Verification & Screenshots (State Machine Audit Log)
```

### Application State Machine
- `CREATED`: Automation run record initialized
- `OPENING`: Launching Playwright browser & opening application start URL
- `INSPECTING`: Extracting structured input element metadata from DOM
- `ANALYZING` & `PLANNING`: Classifying fields and generating validated action plan
- `FILLING`: Executing `FILL`, `SELECT`, `CHECK`, `UPLOAD` actions
- `VERIFYING`: Verifying step completion and advancing page
- `PAUSED`: Paused for human intervention (CAPTCHA, screening questions requiring reasoning, missing profile data, low confidence)
- `READY_FOR_REVIEW`: Reached final review page (stopped safely before submission)
- `FAILED`: Failure state recorded with debug message

### Safety Rules & Automation Boundaries
1. **Local Testbed Only**: Automated form entry operates strictly against local synthetic mock pages (`/mock/apply/*`). Real external platform automation is prohibited.
2. **No Anti-Bot Evasion**: CAPTCHA bypass, stealth fingerprinting, automated authentication, and login bypass are NOT implemented.
3. **No Automatic Final Submission**: The agent stops safely at `READY_FOR_REVIEW`.




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
