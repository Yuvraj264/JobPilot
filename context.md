# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 4 — Job Source Architecture & Job Discovery Foundation (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator, pypdf 6.16+, python-docx 1.2+, python-multipart
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API
- **Frontend**: React 18 (Vite) status, profile, resume, and job discovery management interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) implement `JobSourceAdapter`.
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval (`require_approval_before_submission = True` by default).
- **Strict Truthfulness**: AI screening question answers and tailored resumes draw exclusively from user profile facts.
- **Platform-Independent Discovery**: Internal systems interact exclusively with normalized `Job` records rather than platform-specific site layouts.
- **Deterministic Normalization & Deduplication**: Jobs are normalized (location, employment type, workplace type) and deduplicated (URL, external ID, cross-source company+title match) without AI embeddings.
- **Compliance & Safety Boundary**: Adapters declare compliance metadata (`automation_allowed`, `requires_human_interaction`). Placeholder adapters (`linkedin.py`, `indeed.py`, `company_careers.py`) raise `NotImplementedError` in this phase to prevent unauthorized scraping or anti-bot evasion.

## 4. Completed Work
### Phase 1 — Project Foundation
- [x] Base directory structure, FastAPI app, Docker Compose PostgreSQL, Alembic, Playwright launcher.

### Phase 2 — User Profile & Preference Engine
- [x] Database models (`UserProfile`, `Education`, `Skill`, `Project`, `Certification`, `JobPreference`, `ApplicationPreference`).
- [x] Profile CRUD services, deterministic completeness calculator (0-100%), compact summary endpoint, dev seed generator, React UI, test suite.

### Phase 3 — Resume Management & Resume Intelligence
- [x] Database models (`Resume`, `ResumeSkill`, `ResumeEducation`, `ResumeExperience`, `ResumeProject`, `ResumeCertification`, `ResumeProcessingEvent`).
- [x] `StorageService` for file saving, size checks (10MB max), path traversal defense.
- [x] Text extraction pipeline (`pypdf`, `python-docx`), layered parser, `ConsistencyService`, `QualityService`, REST API, React UI, test suite.

### Phase 4 — Job Source Architecture & Job Discovery Foundation
- [x] Database models (`JobSource`, `RawJob`, `Job`, `JobDiscoveryRun`).
- [x] `JobSourceAdapter` abstract base class and central `JobSourceRegistry`.
- [x] `MockJobSourceAdapter` reading synthetic jobs from `tests/fixtures/jobs.json` with pagination.
- [x] Placeholder adapters (`linkedin`, `indeed`, `company_careers`) raising `NotImplementedError`.
- [x] Normalization engine (`JobNormalizer`, `LocationNormalizer`, `EmploymentTypeNormalizer`, `WorkplaceTypeNormalizer`).
- [x] `JobDeduplicator` handling exact duplicate URLs and cross-source potential duplicates.
- [x] `JobDiscoveryService` orchestrating discovery runs, saving raw payloads, handling partial failures, and logging audit runs.
- [x] REST API mounted at `/api/jobs` (list, search, detail, status patch, sources, discover, stats, runs).
- [x] Alembic migration `221fac96b4fb_create_job_tables.py` applied.
- [x] React frontend `JobDiscoveryManager.jsx` component integrated into `App.jsx`.
- [x] Synthetic fixture (`jobs.json`) and complete test suite (`42 passed in 3.88s`).

## 5. Security & Safety Decisions
- Real scraping or browser automation on external platforms is explicitly forbidden in Phase 4.
- Mock adapter (`mock`) is currently the sole active discovery source.
- Anti-bot evasion, CAPTCHA bypassing, credential scraping, and rate limit evasion are strictly prohibited.

## 6. Known Limitations
- Real LinkedIn / Indeed integrations are not implemented yet (placeholders raise `NotImplementedError`).
- Semantic AI job matching belongs to future phases.

## 7. Next Phase
- **PHASE 5 — Job Matching & Intelligent Job Selection**: Core evaluation engine matching profile skills/experience against job requirements.
