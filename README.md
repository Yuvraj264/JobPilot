# JobPilot — AI-Assisted Job Application Automation Platform

JobPilot is an AI-assisted job application automation platform designed to discover jobs, evaluate fit, tailor application materials truthfully, automate form completion safely with human approval checkpoints, and track applications.

> **CRITICAL SAFETY DIRECTIVE**:
> JobPilot operates under strict human-in-the-loop safety principles. Real-world job platform submission (LinkedIn, Indeed, etc.), CAPTCHA bypass, stealth browser techniques, anti-bot evasion, and automated submission without explicit human approval are strictly prohibited. All submissions target the Phase 6 local mock application environment (`/mock/apply/*`).

---

- ## Complete Project Lifecycle & Architecture (Phases 1–12)
- 
- - **Phase 1 — Project Foundation**: FastAPI backend (`http://localhost:8000`), PostgreSQL Docker Compose setup (`localhost:5433`), Alembic migration infrastructure, Playwright Chromium environment, minimal React frontend (`http://localhost:5173`), and pytest test suite.
- - **Phase 2 — User Profile & Preference Engine**: Canonical user profile schema, job preferences, application preferences, 0-100% completeness engine, and REST API.
- - **Phase 3 — Resume Management & Resume Intelligence**: Multi-resume architecture, secure storage service, PDF/DOCX text extraction, layered resume parser, consistency & quality audit services, and REST API.
- - **Phase 4 — Job Source Architecture & Discovery Foundation**: Adapter-based job discovery framework (`JobSourceAdapter`), central registry, `MockJobSourceAdapter`, job normalizer, deduplicator, and REST API.
- - **Phase 5 — Job Matching & Intelligent Selection**: `JobMatch`, `MatchRun`, and `MatchConfig` models, multi-factor scoring engine (Skills, Location, Salary, Experience, Education, Role, Semantic fit), eligibility engine, and REST API.
- - **Phase 6 — Mock Application Environment & Application Agent Foundation**: Local mock application server (`/mock/apply/*`), Playwright `BrowserController`, `FormAnalyzer`, `ProfileFieldMapper`, `ActionPlanner`, `ActionExecutor`, and `ApplicationAgent` state machine.
- - **Phase 7 — Intelligent Form Understanding & Screening Question Engine**: `QuestionClassifier`, `AnswerSourceResolver`, `AnswerLengthConstraint`, `AnswerGenerator` with **Strict Anti-Fabrication Safeguards**, `AnswerValidator`, `QuestionProcessingService`, and screening review queue.
- - **Phase 8 — Job-Specific Resume Tailoring & Application Package Generation**: `JobRequirementExtractor`, `EvidenceSelector` (strength rating), `ResumeTailoringPlan`, `ResumeKeywordAnalyzer`, `ResumeTruthfulnessValidator` (mandatory anti-fabrication validator), `ChangeTracker`, `StandardPDFRenderer`, `StandardDOCXRenderer`, and `ApplicationPackageService`.
- - **Phase 9 — Application Package, Human Approval & Submission Control Layer**: `Application`, `ApplicationSnapshot`, `PackageVersion`, `ApplicationApproval`, `SubmissionAuthorization`, `SubmissionRun`, and `ApplicationAuditLog` models, `ApplicationValidationService` (blocking vs warnings), `ApplicationApprovalService` (explicit confirmation), `SubmissionAuthorizationService` (time-bound tokens), `SubmissionStateMachine`, `MockSubmissionAdapter`, `SubmissionEngine`, `ApplicationAuditService` (timeline synthesis), and React `ApplicationControlManager`.
- - **Phase 10 — Real Job Source Discovery & Platform Adapter Integration**: `SourceConfiguration` model, `CompanyCareersJobSourceAdapter` (JSON-LD parsing, DOM CSS scraping, Greenhouse and Lever APIs), compliance matrices, standard error classification, token-based Jaccard similarity deduplication, freshness engine, async URL verification checks, and configuration UI.
- - **Phase 11 — Real Application Adapter Framework & Human-Assisted Application Execution**: Generic Application Adapter, anti-bot checkpoints detector, visual human login and CAPTCHA intervention pause/resume controls, target domain validation safety rules.
- - **Phase 12 — Autonomous Job Application Orchestration, Scheduling, Monitoring & Analytics**: Orchestrator runner daemon, job selection/cooldown duplicate checker, transient error retry manager, monitor health metrics, conversion metrics pipeline dashboard, and React UI.
- 
- ---
- 
- ## API Endpoints (Version 1.0.0)
- 
- ### Job Discovery & Ingestion API (`/api/jobs`)
- - `GET /api/jobs/sources` — List all registered job sources.
- - `GET /api/jobs/sources/{source_name}` — Get single source details.
- - `GET /api/jobs/sources/{source_name}/config` — Get source setup configuration settings.
- - `PATCH /api/jobs/sources/{source_name}/config` — Update source setup configuration settings.
- - `POST /api/jobs/sources/{source_name}/enable` — Enable source.
- - `POST /api/jobs/sources/{source_name}/disable` — Disable source.
- - `POST /api/jobs/discover` — Ingest jobs from all enabled sources.
- - `POST /api/jobs/discover/{source_name}` — Ingest jobs from a specific source.
- - `POST /api/jobs/verify-urls` — Trigger async URL reachability verification.
- 
- ### Application Control API (`/api/applications`)
- - `POST /api/applications` — Initialize application record from package.
- - `GET /api/applications` — List all applications.
- - `GET /api/applications/{id}` — Get single application details.
- - `GET /api/applications/{id}/timeline` — Get human-readable chronological event timeline.
- - `POST /api/applications/{id}/validate` — Run validation pipeline (BLOCKING vs WARNING issues).
- - `POST /api/applications/{id}/review` — Request human review.
- - `POST /api/applications/{id}/approve` — Explicit human approval (requires explicit confirmation).
- - `POST /api/applications/{id}/reject` — Reject application.
- - `POST /api/applications/{id}/request-changes` — Request changes.
- - `POST /api/applications/{id}/authorize-submission` — Issue time-bound submission authorization token.
- - `POST /api/applications/{id}/revoke-authorization` — Revoke submission authorization.
- - `POST /api/applications/{id}/submit` — Execute submission engine (with mandatory server-side security checks).
- - `GET /api/applications/{id}/submission` — Get submission run execution log.
- - `GET /api/applications/{id}/audit` — Get raw immutable audit logs.
- 
- ---
- 
- ## Testing & Verification
- 
- Run backend test suite:
- ```bash
- source .venv/bin/activate
- PYTHONPATH=backend:browser-agent pytest tests/
- ```
- All **100 automated tests** passing.
- 
- Run frontend build:
- ```bash
- cd frontend
- npm run build
- ```
- Vite build completes cleanly.
