# JobPilot — Project Roadmap & Flow

This document details the planned development sequence for **JobPilot**, an AI-assisted job application automation platform.

---

## Development Phases

### Phase 1 — Project Foundation
**Status**: COMPLETED
- Basic directory structure (`backend`, `browser-agent`, `frontend`, `tests`, `docs`)
- FastAPI initialization with root (`/`) and health check (`/health`) endpoints
- Centralized configuration system (`app/config.py`) and `.env.example`
- Docker Compose setup for persistent PostgreSQL database (`docker-compose.yml`)
- SQLAlchemy engine & session infrastructure (`app/database/connection.py`)
- Alembic migration environment setup (`alembic.ini`, `alembic/`)
- Playwright environment verification & minimal browser agent files (`browser.py`, `agent.py`, `inspector.py`, `actions.py`)
- Minimal React frontend placeholder verifying backend status
- Basic automated tests for FastAPI, config, database, and Playwright

---

### Phase 2 — User Profile
**Status**: COMPLETED
- Structured database models (`User`, `UserProfile`, `Education`, `Skill`, `Project`, `Certification`, `JobPreference`, `ApplicationPreference`)
- Pydantic V2 schemas with strict field validation (email, non-negative numbers, date ordering, non-empty fields)
- RESTful profile API router (`/api/profile`) with sub-resource endpoints for education, skills, projects, certifications, and preferences
- Deterministic profile completeness calculation engine (0-100%) and missing section identification
- Compact profile summary endpoint (`/api/profile/summary`) for future AI matching engine
- Development sample seed data generator (`POST /api/profile/seed`)
- Alembic database migration applied to PostgreSQL database
- React profile management UI component (`ProfileManager.jsx`)
- Pytest test suite for profile CRUD, validation rules, completeness scoring, and summary generation

### Phase 3 — Resume Management & Resume Intelligence
**Status**: COMPLETED
- Multi-resume architecture (`Resume`, `ResumeSkill`, `ResumeEducation`, `ResumeExperience`, `ResumeProject`, `ResumeCertification`, `ResumeProcessingEvent`)
- Secure `StorageService` with filename UUID generation, size checks (10MB max), PDF/DOCX extension & MIME validation, and path traversal defense
- Text extraction pipeline supporting PDF (`pypdf`) and DOCX (`python-docx`), with image-only scanned PDF detection
- Layered parser: Layer 1 `DeterministicParser` (regex headers, contact info, skills dictionary, education, experience, projects, certifications) + Layer 2 `AIProvider` interface & `LocalMockAIProvider` fallback
- Resume processing state machine (`UPLOADED -> PROCESSING -> PROCESSED` / `FAILED`) with step logging
- `ConsistencyService` comparing canonical UserProfile vs Parsed Resume for mismatch findings
- `QualityService` calculating deterministic 0-100 quality score and actionable suggestions
- Complete REST API router mounted at `/api/resumes` including upload, download, status, parsed, quality, consistency, set-default, reprocess, and delete
- Alembic database migration (`477544d0eea4_create_resume_tables.py`) applied to PostgreSQL
- React frontend resume manager component (`ResumeManager.jsx`) integrated into `App.jsx`
- Synthetic PDF and DOCX test fixtures (`tests/fixtures/`) and 30-test automated test suite

### Phase 4 — Job Source Architecture
**Status**: PLANNED
- Define `JobSourceAdapter` interface and pluggable architecture
- Define `JobSource` data schema

### Phase 5 — Job Discovery and Normalization
**Status**: PLANNED
- Job ingestion pipeline and data normalization into unified `Job` schema

### Phase 6 — Job Matching Engine
**Status**: PLANNED
- Core evaluation engine matching profile skills/experience against job requirements

### Phase 7 — Mock Application Environment
**Status**: PLANNED
- Local testbed server with mock job application forms for safe end-to-end testing

### Phase 8 — Browser Automation Engine
**Status**: PLANNED
- Playwright-based browser driver for navigation, typing, clicking, and file upload

### Phase 9 — Form Understanding
**Status**: PLANNED
- Inspection and semantic categorization of application form fields

### Phase 10 — AI Screening Questions
**Status**: PLANNED
- Generation of truthful screening responses based strictly on user profile data

### Phase 11 — Resume Tailoring
**Status**: PLANNED
- Truthful highlighting and formatting adjustments per job description

### Phase 12 — Human Approval
**Status**: PLANNED
- Mandatory human review and approval checkpoint before application submission

### Phase 13 — Application Tracking
**Status**: PLANNED
- Application state tracking database (`Application`, `ApplicationAnswer`, `AutomationRun`)

### Phase 14 — Real Job-Source Adapters
**Status**: PLANNED
- Permitted source adapters adhering to safety and authentication standards

### Phase 15 — Reliability, Security and Deployment
**Status**: PLANNED
- Security hardening, audit logs, rate-limiting, error handling, and production deployment
