# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 6 — Mock Application Environment & Application Agent Foundation (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator, pypdf 6.16+, python-docx 1.2+, python-multipart
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API (Chromium wrapper, non-stealth, full DOM inspection, screenshot capture)
- **Frontend**: React 18 (Vite) status, profile, resume, job discovery, match dashboard, and automation monitor interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) implement `JobSourceAdapter`.
- **Application Target Abstraction**: Application agent interacts exclusively via generic `ApplicationTarget` interface (`MockApplicationTarget`, placeholders `LinkedInApplicationTarget`, `IndeedApplicationTarget`, `CompanyCareerApplicationTarget`).
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval checkpoint before final submission (`READY_FOR_REVIEW`). Agent pauses (`PAUSED`) when encountering CAPTCHAs, screening questions requiring human reasoning, missing profile data, or low confidence.
- **Strict Fail-Safe Automation**: Browser agent executes ONLY actions represented by an approved action schema (`FILL`, `SELECT`, `CHECK`, `UNCHECK`, `UPLOAD`, `CLICK`, `WAIT`, `PAUSE_FOR_HUMAN`, `VERIFY`). Never executes arbitrary LLM JS/shell scripts or anti-bot evasions.
- **Strict Truthfulness**: Answers and form values draw exclusively from user profile facts without inventing fake values (`MISSING_DATA` state).
- **Deterministic Match Explanations**: Scores and recommendations generate structured human-readable explanations (`summary`, `strengths`, `concerns`) strictly from deterministic match facts without opaque AI black boxes.
- **Hard Eligibility vs Soft Preferences**: Hard constraints (experience bounds, work authorization, relocation refusal) force `SKIP` recommendations regardless of semantic score.
- **Offline Fallback Architecture**: `SemanticMatcher` provides `LocalEmbeddingProvider` text similarity (n-grams/Jaccard) without requiring paid external LLM APIs.

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

### Phase 6 — Mock Application Environment & Application Agent Foundation
- [x] Local synthetic mock application server (`/mock/jobs`, `/mock/apply/{id}/step/1`, `/step/2`, `/step/3`, `/review`, `/captcha`).
- [x] Generic `ApplicationTarget` base class and `MockApplicationTarget` implementation.
- [x] `BrowserController` Playwright Chromium wrapper (launch, navigate, screenshot capture, DOM inspection).
- [x] `PageInspector` extracting structured DOM element objects without raw HTML API leakage.
- [x] `FormAnalyzer` classifying form controls into semantic field types using deterministic heuristics.
- [x] `ProfileFieldMapper` mapping semantic fields to profile/resume facts with confidence scores and `MISSING_DATA` handling.
- [x] `ApplicationActionPlanner` generating validated action plans with `PAUSE_FOR_HUMAN` triggers.
- [x] `ApplicationActionExecutor` using 5-tier selector priority, logging `ActionLog` entries, and capturing screenshots.
- [x] Application State Machine (`CREATED -> OPENING -> INSPECTING -> ANALYZING -> PLANNING -> FILLING -> VERIFYING -> PAUSED / READY_FOR_REVIEW / FAILED`).
- [x] Database models (`AutomationRun`, `ActionLog`).
- [x] REST API router mounted at `/api/automation` (`/run`, `/runs`, `/runs/{id}`, `/runs/{id}/resume`, `/pause`, `/actions`, `/screenshots`).
- [x] Alembic migration `c9dc6936452f_create_automation_tables.py` applied to PostgreSQL.
- [x] React frontend component `AutomationMonitorManager.jsx` integrated into `App.jsx`.
- [x] Automated test suite (`60 passed in 13.40s`) including 7 mock failure scenarios and end-to-end browser automation pipeline reaching `READY_FOR_REVIEW`.

## 5. Security & Automation Boundaries
- **No External Platform Automation**: Real LinkedIn, Indeed, or career site scraping/form filling is strictly prohibited in Phase 6.
- **No Anti-Bot Evasion**: CAPTCHA bypass, stealth fingerprinting, automated authentication, and login bypass are NOT implemented.
- **Fail-Safe Stopping**: Agent stops safely at `READY_FOR_REVIEW` or `PAUSED` without submitting applications automatically.

## 6. Next Phase
- **Phase 7 — Intelligent Form Understanding & Screening Question Engine**: Semantic question understanding, classification, and truthful screening question response generation.
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
