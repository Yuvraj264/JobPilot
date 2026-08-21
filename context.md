# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 2 — User Profile & Preference Engine (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API
- **Frontend**: React 18 (Vite) status & profile management interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) will implement `JobSourceAdapter`.
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval (`require_approval_before_submission = True` by default).
- **Strict Truthfulness**: AI screening question answers and tailored resumes draw exclusively from user profile facts.
- **Normalized Profile Architecture**: Relational SQL design with dedicated child tables for Education, Skills, Projects, Certifications, Job Preferences, and Application Preferences.
- **Deterministic Completeness Scoring**: Profile completeness (0-100%) calculated deterministically without AI dependency.

## 4. Completed Work
### Phase 1 — Project Foundation
- [x] Directory structure (`backend/`, `browser-agent/`, `frontend/`, `tests/`, `docs/`).
- [x] FastAPI base app with `/` and `/health` endpoints.
- [x] Docker Compose PostgreSQL setup.
- [x] Alembic migration environment.
- [x] Playwright Chromium browser launch verification.

### Phase 2 — User Profile & Preference Engine
- [x] Created database models: `User`, `UserProfile`, `Education`, `Skill`, `Project`, `Certification`, `JobPreference`, `ApplicationPreference`.
- [x] Created Pydantic V2 request & response schemas with strict validation rules (valid email format, non-negative years of experience / salary, `end_year >= start_year`, `expiry_date >= issue_date`, non-empty names).
- [x] Created `ProfileService` handling database CRUD queries for profile and all sub-entities.
- [x] Created `CompletenessService` implementing a deterministic completeness scoring algorithm (0-100%) and missing section identification.
- [x] Created `GET /api/profile/summary` endpoint providing a compact structured representation of the profile for future AI matching engines.
- [x] Created `seed_sample_profile()` service and `POST /api/profile/seed` endpoint for dev data generation.
- [x] Created & executed Alembic migration (`765dd9b84ef3_create_user_profile_tables.py`).
- [x] Built React profile management UI component (`ProfileManager.jsx`).
- [x] Built test suite covering profile CRUD, sub-resource CRUD, validation edge cases, completeness calculation, and profile summary structure (`20 passed in 1.88s`).

## 5. Important Decisions
- **Relational Normalized Design**: Child entities (skills, education, projects, certifications) are stored in dedicated relational tables with foreign keys and cascade delete rules rather than flat text strings or arrays in main profile.
- **Default Safety Preference**: `require_approval_before_submission` defaults to `True`.
- **Dev Seed Endpoint**: `POST /api/profile/seed` generates realistic fake test data (`Test User`).

## 6. Known Limitations
- Initial design focuses on single authenticated user context (`user_id = 1`), while database architecture natively supports multi-user extension via `users` table FKs.

## 7. Next Phase
- **PHASE 3 — Resume Management & Resume Intelligence**: Document upload, parsing, text extraction, resume section indexing, and resume versioning.
