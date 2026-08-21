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

### Phase 4 — Job Source Architecture & Job Discovery Foundation
**Status**: COMPLETED
- Pluggable `JobSourceAdapter` interface (`base.py`) with compliance metadata (`automation_allowed`, `requires_human_interaction`, `notes`)
- Central `JobSourceRegistry` (`registry.py`) providing registration, lookup, source listing, and dynamic enable/disable controls
- Relational database schema (`JobSource`, `RawJob`, `Job`, `JobDiscoveryRun`)
- `MockJobSourceAdapter` generating synthetic jobs from `tests/fixtures/jobs.json` with pagination support
- Placeholder adapters (`LinkedInJobSourceAdapter`, `IndeedJobSourceAdapter`, `CompanyCareersJobSourceAdapter`) raising `NotImplementedError`
- Normalization engine (`JobNormalizer`, `LocationNormalizer`, `EmploymentTypeNormalizer`, `WorkplaceTypeNormalizer`)
- Deduplication engine (`JobDeduplicator`) identifying exact duplicates (URL/external ID) and flagging cross-source matches as `POTENTIAL_DUPLICATE`
- Ingestion engine (`JobDiscoveryService`) executing discovery runs, storing raw payloads, handling partial malformed job failures without halting runs, and tracking audit logs
- REST API endpoints mounted at `/api/jobs` for job catalog listing, search, details, status updates, sources management, mock discovery execution, and statistics
- Alembic database migration (`221fac96b4fb_create_job_tables.py`) applied to PostgreSQL
- React frontend job discovery manager component (`JobDiscoveryManager.jsx`) integrated into `App.jsx`
- Complete automated test suite (`42 passed in 3.88s`) including unit tests and end-to-end discovery pipeline verification

### Phase 5 — Job Matching & Intelligent Job Selection
**Status**: COMPLETED
- `EligibilityEngine` evaluating hard constraints (minimum experience bounds, work authorization/sponsorship, location/relocation constraints) vs soft preferences
- Component matchers: `SkillMatcher` (required vs preferred skill extraction & normalization), `RoleMatcher` (taxonomy & synonym matching), `LocationMatcher` (city equivalence & remote matching), `EmploymentMatcher`, `WorkplaceMatcher`, `SalaryMatcher` (missing salary no-penalty logic), `ExperienceMatcher`, `EducationMatcher`
- `SemanticMatcher` with `LocalEmbeddingProvider` fallback (n-gram/token similarity) avoiding paid commercial API dependencies
- `ExplanationGenerator` producing deterministic human-readable structured explanations (`summary`, `strengths`, `concerns`)
- `ScoringEngine` computing weighted score (0-100), confidence (0.0-1.0), and `APPLY`/`REVIEW`/`SKIP` recommendations based on eligibility and user thresholds
- Relational database schema (`JobMatch`, `MatchRun`, `MatchConfig`)
- `JobMatchingService` orchestrating single job matching, batch matching runs, statistics calculation, and config management
- REST API router mounted at `/api/matching` (`/job/{id}`, `/jobs`, `/run`, `/runs`, `/stats`, `/config`)
- Alembic database migration (`efc71220df35_create_matching_tables.py`) applied to PostgreSQL
- React frontend match dashboard component (`MatchDashboardManager.jsx`) integrated into `App.jsx`
- Automated test suite (`53 passed in 4.07s`) including unit tests and end-to-end matching pipeline verification

### Phase 6 — Mock Application Environment & Application Agent Foundation
**Status**: COMPLETED
- Synthetic local mock application server (`/mock/jobs`, `/mock/apply/{id}/step/1`, `/step/2`, `/step/3`, `/review`, `/captcha`)
- Generic `ApplicationTarget` abstraction (`MockApplicationTarget`, placeholders `LinkedInApplicationTarget`, `IndeedApplicationTarget`, `CompanyCareerApplicationTarget`)
- Centralized `BrowserController` Playwright Chromium wrapper (launch, navigate, screenshot capture, DOM inspection, page state retrieval)
- `PageInspector` extracting structured element objects (forms, inputs, selects, textareas, radio groups, checkboxes, file inputs)
- `FormAnalyzer` classifying controls into semantic field types (`PERSONAL_NAME`, `EMAIL`, `PHONE`, `LOCATION`, `DEGREE`, `INSTITUTION`, `GRADUATION_YEAR`, `EXPERIENCE`, `CURRENT_ROLE`, `SKILLS`, `SALARY`, `RELOCATION`, `RESUME`, `SCREENING_QUESTION`, `UNKNOWN`)
- `ProfileFieldMapper` mapping semantic fields to user profile and default resume data with confidence scores and `MISSING_DATA` handling without fabricating values
- `ApplicationActionPlanner` generating validated action plans (`FILL`, `SELECT`, `CHECK`, `UNCHECK`, `UPLOAD`, `CLICK`, `WAIT`, `PAUSE_FOR_HUMAN`, `VERIFY`)
- `ApplicationActionExecutor` using 5-tier selector priority, executing validated schemas, verifying outcomes, recording `ActionLog` entries, and capturing screenshots
- State Machine (`CREATED -> OPENING -> INSPECTING -> ANALYZING -> PLANNING -> FILLING -> VERIFYING -> PAUSED / READY_FOR_REVIEW / FAILED`)
- Relational database schema (`AutomationRun`, `ActionLog`)
- REST API router mounted at `/api/automation` (`/run`, `/runs`, `/runs/{id}`, `/runs/{id}/resume`, `/pause`, `/actions`, `/screenshots`)
- Alembic database migration (`c9dc6936452f_create_automation_tables.py`) applied to PostgreSQL
- React frontend automation monitor component (`AutomationMonitorManager.jsx`) integrated into `App.jsx`
- Automated test suite (`60 passed in 13.40s`) including unit tests, 7 mock failure scenarios, and end-to-end browser automation pipeline verification reaching `READY_FOR_REVIEW`

---

### Phase 7 — Intelligent Form Understanding & Screening Question Engine
**Status**: COMPLETED
- Controlled Question Taxonomy (`PERSONAL_INFORMATION`, `EDUCATION`, `EXPERIENCE`, `SKILL`, `PROJECT`, `CERTIFICATION`, `SALARY`, `LOCATION`, `RELOCATION`, `WORK_AUTHORIZATION`, `SPONSORSHIP`, `WORKPLACE_PREFERENCE`, `EMPLOYMENT_TYPE`, `AVAILABILITY`, `NOTICE_PERIOD`, `MOTIVATION`, `ROLE_INTEREST`, `COMPANY_INTEREST`, `STRENGTH`, `WEAKNESS`, `ACHIEVEMENT`, `BEHAVIORAL`, `TECHNICAL`, `GENERAL_OPEN_ENDED`, `UNKNOWN`)
- `QuestionClassifier` categorizing question text, labels, input types, and surrounding job context with confidence scoring (returns `UNKNOWN` with confidence < 0.70 to trigger human review)
- `AnswerSourceResolver` resolving answer source (`PROFILE`, `RESUME`, `JOB_DESCRIPTION`, `COMPANY_CONTEXT`, `DETERMINISTIC_RULE`, `AI_GENERATED`, `HUMAN`, `GENERAL_KNOWLEDGE`)
- `AnswerLengthConstraint` extracting and enforcing character/word limits from HTML `maxlength` attributes or prompt text without truncating text mid-sentence
- `ScreeningAIProvider` abstraction with `LocalMockScreeningAIProvider` fallback producing grounded answers using local n-gram/template context synthesis without paid LLM API cost
- `AnswerGenerator` with **Strict Anti-Fabrication Safeguards**: checks profile/resume evidence for requested skills/experience (AWS, Selenium, leadership), returning `INSUFFICIENT_INFORMATION` and requiring human review when unpopulated
- `AnswerValidator` verifying non-empty text, length limits, factual grounding, and prohibited claims
- `QuestionProcessingService` orchestrating the screening pipeline and managing reusable `AnswerMemory`
- Browser `ApplicationAgent` integration: screening questions are classified, validated, and auto-filled if confidence >= threshold, or paused (`PAUSED`) and populating the human review queue
- Relational database schema (`ApplicationQuestion`, `ApplicationAnswer`, `AnswerMemory`)
- REST API router mounted at `/api/questions` and `/api/answers` (`/analyze`, `/review`, `/{id}`, `/{id}/answer`, `/{id}/approve`, `/{id}/reject`, `/{id}/validate`)
- Alembic database migration (`2ba72b12c4b6_create_screening_question_tables.py`) applied to PostgreSQL
- React frontend review queue component (`ScreeningReviewQueueManager.jsx`) integrated into `App.jsx`
- Automated test suite (`66 passed in 16.60s`) including unit tests, mandatory anti-fabrication safeguard tests, 8 mock scenarios, and end-to-end screening question pipeline integration

---

### Phase 8 — Job-Specific Resume Tailoring & Application Package Generation
**Status**: PLANNED
- Job-specific resume tailoring, keyword alignment, and customized application package generation

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
