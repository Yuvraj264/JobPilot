# JobPilot — Project Context & State

## 1. Project Information
- **Project Name**: JobPilot
- **Objective**: AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.
- **Current Phase**: Phase 7 — Intelligent Form Understanding & Screening Question Engine (COMPLETED)

## 2. Technology Stack
- **Backend Framework**: Python 3.14, FastAPI 0.141+, Pydantic V2, Uvicorn, email-validator, pypdf 6.16+, python-docx 1.2+, python-multipart
- **Database Layer**: PostgreSQL 15 (Docker Compose on port 5433), SQLAlchemy 2.0 ORM, Alembic migrations
- **Browser Automation**: Playwright Python API (Chromium wrapper, non-stealth, full DOM inspection, screenshot capture)
- **Frontend**: React 18 (Vite) status, profile, resume, job discovery, match dashboard, automation monitor, and screening review queue interface
- **Environment Management**: Docker Compose, `.env`, `.env.example`, Pytest

## 3. Architectural Principles
- **Adapter Pattern for Job Sources**: All job sources (company career sites, permitted platforms) implement `JobSourceAdapter`.
- **Application Target Abstraction**: Application agent interacts exclusively via generic `ApplicationTarget` interface (`MockApplicationTarget`, placeholders `LinkedInApplicationTarget`, `IndeedApplicationTarget`, `CompanyCareerApplicationTarget`).
- **Human-in-the-Loop Safeguards**: Applications require explicit human approval checkpoint before final submission (`READY_FOR_REVIEW`). Agent pauses (`PAUSED`) when encountering CAPTCHAs, screening questions requiring human reasoning/approval, missing profile data, or low confidence.
- **Strict Anti-Fabrication Safeguard**: AI Screening Question Engine NEVER fabricates experience, credentials, or skills. If profile/resume evidence is unpopulated, returns `INSUFFICIENT_INFORMATION` and requires human review (`NEEDS_REVIEW`).
- **Strict Fail-Safe Automation**: Browser agent executes ONLY actions represented by an approved action schema (`FILL`, `SELECT`, `CHECK`, `UNCHECK`, `UPLOAD`, `CLICK`, `WAIT`, `PAUSE_FOR_HUMAN`, `VERIFY`).
- **Offline Fallback Architecture**: `ScreeningAIProvider` and `SemanticMatcher` provide local n-gram/template context synthesis without requiring paid external LLM APIs.

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
- [x] `BrowserController` Playwright Chromium wrapper.
- [x] `PageInspector` extracting structured DOM element objects.
- [x] `FormAnalyzer` classifying form controls into semantic field types.
- [x] `ProfileFieldMapper` mapping semantic fields to profile/resume facts.
- [x] `ApplicationActionPlanner` generating validated action plans.
- [x] `ApplicationActionExecutor` using 5-tier selector priority and logging `ActionLog` entries.
- [x] Application State Machine (`CREATED -> OPENING -> INSPECTING -> ANALYZING -> PLANNING -> FILLING -> VERIFYING -> PAUSED / READY_FOR_REVIEW / FAILED`).
- [x] Database models (`AutomationRun`, `ActionLog`).
- [x] REST API router mounted at `/api/automation`.
- [x] Alembic migration `c9dc6936452f_create_automation_tables.py` applied to PostgreSQL.
- [x] React frontend component `AutomationMonitorManager.jsx` integrated into `App.jsx`.

### Phase 7 — Intelligent Form Understanding & Screening Question Engine
- [x] Controlled Question Taxonomy (`QuestionType` enum).
- [x] `QuestionClassifier` categorizing questions with confidence scores.
- [x] `AnswerSourceResolver` resolving source (`PROFILE`, `RESUME`, `JOB_DESCRIPTION`, `COMPANY_CONTEXT`, `DETERMINISTIC_RULE`, `AI_GENERATED`, `HUMAN`, `GENERAL_KNOWLEDGE`).
- [x] `AnswerLengthConstraint` enforcing character/word limits without sentence clipping.
- [x] `ScreeningAIProvider` interface & `LocalMockScreeningAIProvider` fallback.
- [x] `AnswerGenerator` with **Strict Anti-Fabrication Safeguards**: returns `INSUFFICIENT_INFORMATION` when candidate evidence is missing.
- [x] `AnswerValidator` validating non-empty status, length bounds, and confidence.
- [x] `QuestionProcessingService` orchestrating pipeline and managing `AnswerMemory`.
- [x] Browser `ApplicationAgent` integration: auto-fills validated answers or pauses for human review.
- [x] Database models (`ApplicationQuestion`, `ApplicationAnswer`, `AnswerMemory`).
- [x] REST API router mounted at `/api/questions` and `/api/answers`.
- [x] Alembic migration `2ba72b12c4b6_create_screening_question_tables.py` applied to PostgreSQL.
- [x] React frontend component `ScreeningReviewQueueManager.jsx` integrated into `App.jsx`.
- [x] Automated test suite (`66 passed in 16.60s`) including unit tests, mandatory anti-fabrication safeguard tests, 8 mock scenarios, and end-to-end integration.

## 5. Security & Automation Boundaries
- **No External Platform Automation**: Real LinkedIn, Indeed, or career site scraping/form filling is strictly prohibited.
- **No Anti-Bot Evasion**: CAPTCHA bypass, stealth fingerprinting, automated authentication, and login bypass are NOT implemented.
- **Fail-Safe Stopping**: Agent stops safely at `READY_FOR_REVIEW` or `PAUSED` without submitting applications automatically.
- **No Answer Fabrication**: AI Screening Question Engine NEVER invents experience or skills.

## 6. Next Phase
- **Phase 8 — Job-Specific Resume Tailoring & Application Package Generation**: Resume tailoring and keyword alignment.
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
