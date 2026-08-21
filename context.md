# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 5 — Job Matching & Intelligent Job Selection (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator, pypdf 6.16+, python-docx 1.2+, python-multipart
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API
- **Frontend**: React 18 (Vite) status, profile, resume, job discovery, and match dashboard interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) implement `JobSourceAdapter`.
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval (`require_approval_before_submission = True` by default).
- **Strict Truthfulness**: AI screening question answers and tailored resumes draw exclusively from user profile facts.
- **Deterministic Match Explanations**: Scores and recommendations generate structured human-readable explanations (`summary`, `strengths`, `concerns`) strictly from deterministic match facts without opaque AI black boxes.
- **Hard Eligibility vs Soft Preferences**: Hard constraints (experience bounds, work authorization, relocation refusal) force `SKIP` recommendations regardless of semantic score.
- **Offline Fallback Architecture**: `SemanticMatcher` provides `LocalEmbeddingProvider` text similarity (n-grams/Jaccard) without requiring paid external LLM APIs.
- **Versioned Match Engine**: Matches record `matcher_version="1.0"` to ensure reproducibility.

## 4. Completed Work
### Phase 1 — Project Foundation
- [x] Base directory structure, FastAPI app, Docker Compose PostgreSQL, Alembic, Playwright launcher.

### Phase 2 — User Profile & Preference Engine
- [x] Database models (`UserProfile`, `Education`, `Skill`, `Project`, `Certification`, `JobPreference`, `ApplicationPreference`).
- [x] Profile CRUD services, completeness calculator (0-100%), compact summary endpoint, dev seed generator, React UI, test suite.

### Phase 3 — Resume Management & Resume Intelligence
- [x] Database models (`Resume`, `ResumeSkill`, `ResumeEducation`, `ResumeExperience`, `ResumeProject`, `ResumeCertification`, `ResumeProcessingEvent`).
- [x] `StorageService` for file saving, size checks (10MB max), path traversal defense.
- [x] Text extraction pipeline (`pypdf`, `python-docx`), layered parser, `ConsistencyService`, `QualityService`, REST API, React UI, test suite.

### Phase 4 — Job Source Architecture & Job Discovery Foundation
- [x] Database models (`JobSource`, `RawJob`, `Job`, `JobDiscoveryRun`).
- [x] `JobSourceAdapter` abstract base class and central `JobSourceRegistry`.
- [x] `MockJobSourceAdapter` reading synthetic jobs from `tests/fixtures/jobs.json` with pagination.
- [x] Normalization engine, `JobDeduplicator`, `JobDiscoveryService`, REST API (`/api/jobs`), React UI, test suite.

### Phase 5 — Job Matching & Intelligent Job Selection
- [x] Database models (`JobMatch`, `MatchRun`, `MatchConfig`).
- [x] `EligibilityEngine` evaluating hard constraints vs soft preferences.
- [x] Component matchers: `SkillMatcher`, `RoleMatcher`, `LocationMatcher`, `EmploymentMatcher`, `WorkplaceMatcher`, `SalaryMatcher`, `ExperienceMatcher`, `EducationMatcher`.
- [x] `SemanticMatcher` with `LocalEmbeddingProvider` fallback.
- [x] `ExplanationGenerator` producing structured facts (`summary`, `strengths`, `concerns`).
- [x] `ScoringEngine` computing weighted score (0-100), confidence, and `APPLY`/`REVIEW`/`SKIP` recommendations.
- [x] `JobMatchingService` orchestrating single matching, batch matching runs, stats, and config.
- [x] REST API endpoints mounted at `/api/matching` (`/job/{id}`, `/jobs`, `/run`, `/runs`, `/stats`, `/config`).
- [x] Alembic migration `efc71220df35_create_matching_tables.py` applied.
- [x] React frontend `MatchDashboardManager.jsx` component integrated into `App.jsx`.
- [x] Automated test suite (`53 passed in 4.07s`).

## 5. Security & Safety Decisions
- Real application form filling or submission is strictly forbidden in Phase 5.
- Job matching evaluates suitability but does NOT submit applications.
- Match explanations are transparently derived from verified profile facts.

## 6. Known Limitations
- Local embedding provider uses token/n-gram similarity; local neural vector database can be attached in future phases.

## 7. Next Phase
- **PHASE 6 — Mock Application Environment & Application Agent Foundation**: Local testbed server with mock job application forms for safe end-to-end browser automation testing.
