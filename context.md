# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 3 — Resume Management & Resume Intelligence (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator, pypdf 6.16+, python-docx 1.2+, python-multipart
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API
- **Frontend**: React 18 (Vite) status, profile, and resume management interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) will implement `JobSourceAdapter`.
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval (`require_approval_before_submission = True` by default).
- **Strict Truthfulness**: AI screening question answers and tailored resumes draw exclusively from user profile facts.
- **Multi-Resume Versioning**: Users can manage multiple tailored resume documents (General, QA, Data Analyst, etc.) without overwriting canonical user identity.
- **Layered Parsing Architecture**: Layer 1 deterministic regex section/keyword extraction + Layer 2 `AIProvider` interface with offline `LocalMockAIProvider` fallback.
- **Isolated Secure Storage**: File storage outside database with path traversal defense, file type validation, and max size limits.

## 4. Completed Work
### Phase 1 — Project Foundation
- [x] Base directory structure, FastAPI app, Docker Compose PostgreSQL, Alembic, Playwright launcher.

### Phase 2 — User Profile & Preference Engine
- [x] Database models (`UserProfile`, `Education`, `Skill`, `Project`, `Certification`, `JobPreference`, `ApplicationPreference`).
- [x] Profile CRUD services, deterministic completeness calculator (0-100%), compact summary endpoint, dev seed generator, React UI, test suite.

### Phase 3 — Resume Management & Resume Intelligence
- [x] Database models (`Resume`, `ResumeSkill`, `ResumeEducation`, `ResumeExperience`, `ResumeProject`, `ResumeCertification`, `ResumeProcessingEvent`).
- [x] `StorageService` for PDF/DOCX saving, safe UUID filenames, size checks (10MB max), path traversal defense, and deletion.
- [x] Text extraction pipeline using `pypdf` for PDF and `python-docx` for DOCX, with scanned/image-only PDF detection.
- [x] Layered `ResumeParser` (Layer 1 `DeterministicParser` + Layer 2 `AIProvider` interface & `LocalMockAIProvider` fallback).
- [x] `ResumeProcessingService` state transition pipeline (`UPLOADED -> PROCESSING -> PROCESSED` / `FAILED`).
- [x] `ConsistencyService` comparing UserProfile vs Resume for mismatch findings.
- [x] `QualityService` for 0-100 quality scoring and suggestions.
- [x] Complete REST API mounted at `/api/resumes` (upload, download, status, parsed, quality, consistency, set-default, reprocess, delete).
- [x] Alembic migration `477544d0eea4_create_resume_tables.py` applied.
- [x] React frontend `ResumeManager.jsx` component.
- [x] Synthetic test fixtures (`tests/fixtures/`) and 30 unit tests (`30 passed in 2.62s`).

## 5. Security & Safety Decisions
- Files stored outside DB in `./storage/resumes` (ignored in `.gitignore`).
- Storage path traversal protection enforced via `StorageService.resolve_path()`.
- Secure download endpoint verifies profile ownership before streaming file.
- Uploaded files are never executed.

## 6. Known Limitations
- OCR is not supported yet (scanned image-only PDFs raise a descriptive error).
- Commercial AI provider integration is abstracted via `AIProvider` interface but defaults to `LocalMockAIProvider`.
- Job-specific resume tailoring belongs to future phases.

## 7. Next Phase
- **PHASE 4 — Job Source Architecture & Job Discovery Foundation**: JobSourceAdapter interface, permitted sources, job schema normalization.
