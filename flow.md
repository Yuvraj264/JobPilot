# JobPilot — Operational Flow

## Overview
JobPilot is an AI-assisted job application automation platform. Its lifecycle flows through 16 completed phases:

```
[Phase 1: Foundation & Infrastructure] — COMPLETED
                   │
                   ▼
[Phase 2: User Profile & Preferences Engine] — COMPLETED
                   │
                   ▼
[Phase 3: Resume Management & Resume Intelligence] — COMPLETED
                   │
                   ▼
[Phase 4: Job Source Architecture & Job Discovery Foundation] — COMPLETED
                   │
                   ▼
[Phase 5: Job Matching & Intelligent Job Selection Engine] — COMPLETED
                   │
                   ▼
[Phase 6: Mock Application Environment & Agent Foundation] — COMPLETED
                   │
                   ▼
[Phase 7: Form Understanding & Screening Question Engine] — COMPLETED
                   │
                   ▼
[Phase 8: Resume Tailoring & Application Package Engine] — COMPLETED
                   │
                   ▼
[Phase 9: Application Package, Approval & Submission Control Layer] — COMPLETED
                   │
                   ▼
[Phase 10: Real Job Source Discovery & Platform Adapter Integration] — COMPLETED
                   │
                   ▼
[Phase 11: Real Application Adapter Framework & Human-Assisted Execution] — COMPLETED
                   │
                   ▼
[Phase 12: Autonomous Job Ingestion & Loop Orchestration] — COMPLETED
                   │
                   ▼
[Phase 15: Staging Verification & Reliability Targets] — COMPLETED
                   │
                   ▼
[Phase 16: Personal Preferences & Feedback Optimization] — COMPLETED
```

---

## Phase 9 Flow: Human Approval & Submission Control Layer

1. **Application Creation & Package Versioning**:
   - Application record created from `ApplicationPackage`. Version 1 snapshot logged.
2. **Validation Pipeline**:
   - `ApplicationValidationService` evaluates target Job, User Profile, Source Resume, Tailored Resume (truthfulness check), and Screening Questions.
   - Categorizes findings into `BLOCKING` vs `WARNING`. Blocking issues prevent advancing to review.
3. **Human Review & Explicit Approval**:
   - Reviewer inspects Job, Match, Resume preview, screening answers, and validation findings.
   - Approval requires explicit user confirmation (`user_confirmed=True`).
4. **Submission Authorization Engine**:
   - `SubmissionAuthorizationService` issues time-bound authorization tokens tied strictly to approved package version.
   - Verifies active, unexpired, unrevoked, and unused token status before allowing submission.
5. **Submission Execution & Verification**:
   - `SubmissionEngine` delegates to `MockSubmissionAdapter` (submitting to local mock portal).
   - Verifies submission ID confirmation before advancing status to `SUBMITTED`.
   - Records point-in-time `ApplicationSnapshot` and logs events to immutable `ApplicationAuditLog`.

---

## Phase 10 Flow: Real Job Source Discovery & Platform Adapter Integration

1. **Job Source Registration & Configuration Setup**:
   - Source metadata and capability matrices are loaded via `registry`.
   - Specific parser configurations (selectors, credentials, limits) are defined in `SourceConfiguration`.
2. **Platform Constraints Enforcement**:
   - LinkedIn and Indeed enforce policy boundaries and reject automated discovery runs with `UNSUPPORTED_OPERATION` or `AUTHENTICATION_REQUIRED`, requiring manual or human-assisted sessions.
3. **Company Career Page Scraping & API Ingestion**:
   - Ingests jobs using Greenhouse/Lever APIs, parsing JSON-LD structured data, or extracting details via visual DOM CSS selectors.
   - Restricts operations according to rate-limiting thresholds (delays, requests/minute limits).
4. **Ingestion & Advanced Deduplication Pipeline**:
   - Raw jobs are normalized into a common Job schema.
   - Cross-source matches are identified using token-overlap Jaccard description similarity and cross-platform external ID comparison, flagging duplicates as `POTENTIAL_DUPLICATE` or `DUPLICATE`.
5. **Freshness Tracking & URL Verification**:
   - Active job listings maintain `ACTIVE` status. Unseen items transition to `STALE` and `EXPIRED` status.
   - Periodic async HTTP GET/HEAD checks update job URL status to `REACHABLE`, `NOT_FOUND`, `REDIRECTED`, or `BLOCKED`.

---

## Phase 11 Flow: Real Application Adapter Framework & Human-Assisted Application Execution

1. **Safety Controls & Allowed Domains Verification**:
   - Execution begins with domain validation against the configuration allowlist. Disallowed domains trigger `DomainValidationError` and immediate worker halt.
   - Restricts daily execution and failed attempts thresholds; runs default to `DRY_RUN = true` and `mode = HUMAN_ASSISTED` to guarantee safety.
2. **Platform Adapter Specialization**:
   - Real platforms (LinkedIn, Indeed) enforce human login checkpoints and declare automated submission capabilities as `UNSUPPORTED`.
   - The generic career adapter navigates forms, analyzes components, maps profile fields, and executes page fills.
3. **Logins & CAPTCHA Pause Mechanisms**:
   - Live visual inspections detect anti-bot elements, log-in prompts, or CAPTCHA challenges.
   - The worker immediately pauses automation, logs a `HumanInterventionEvent` with reasons, and updates the application state to `PAUSED`.
4. **Human Intervention Resolution & Resume**:
   - The user resolves the intervention prompt (solving CAPTCHA or completing log-in) in the browser window, then clicks `[Resume Automation]` in the dashboard.
   - The worker clears active interventions and resumes automated navigation/form filling.
5. **Dry Run Previews & Real Execution Verification**:
   - Dry runs execute all fill actions, save navigation timeline logs and final verification screenshots, but stop safely before clicking submit.
   - Real runs execute field fills, verify confirmation pages and success text patterns, record point-in-time snapshots, and update status to `SUBMITTED`.

---

## Phase 12 Flow: Autonomous Job Application Orchestration, Scheduling, Monitoring & Analytics

1. **Automation Configuration Preset Mapping**:
   - The user selects or updates settings via `AutomationConfiguration`.
   - Critical boundaries: `require_human_review = true`, `max_applications_per_run = 3`, `max_applications_per_day = 10`.
2. **Job Eligibility Filtering & Cooldown Checks**:
   - `JobSelectionService` scans matches for minimum match score (default 80.0) and permitted recommendations.
   - Evaluates active queue states and checks company/title history: items applied within a 30-day window are flagged as `ALREADY_APPLIED` and automatically excluded.
3. **Daily Application Safety Limits**:
   - Limits checks run before every execution step. If the candidate's total applications submitted today hits `max_applications_per_day` or a per-source limit is met, the pipeline cancels run progress.
4. **Crash Checkpoints & Recovery Isolation**:
   - Each orchestration run transitions through states: `RUNNING` -> `COMPLETED`, `FAILED`, or `PARTIAL`.
   - Pipeline checkpoints save states after discovery, matching, package preparation, and execution. If an execution fails or crashes, details are logged without crashing the remaining applications or future runs.
5. **Transient Failure Categorization & Retry Manager**:
   - `RetryManager` classifies error messages: recoverable network or browser crashes trigger a retry attempt (up to `max_retries` limit). Non-recoverable validation or anti-bot checks skip retries.
6. **Analytics Funnel Compilation & Health Checks**:
   - Analytics compilation calculates funnel statistics (discovered -> matched -> selected -> prepared -> submitted -> failed), failure breakdown classifications, and visual browser status checks.

---

## Phase 15 Flow: Real-World Validation, Reliability Testing & Intelligent Optimization

1. **Labor Market & Career Insights Ingestion**:
   - Discovered jobs are aggregated by title, required skills, and locations.
   - User profile skills are compared against overall requirements to compute requested skills and identify skill gaps (missing in profile).
2. **Intelligent Profile Optimization Recommendations**:
   - `OptimizationEngine` checks pipeline errors (failures, timeouts), low keyword coverage on tailored resumes, and screening questions with `INSUFFICIENT_INFORMATION` answers.
   - Generates profile enhancement suggestions to improve candidate matching scores and decrease human interventions.
3. **Outcome & Feedback Quality Loop**:
   - Users manually record ratings (user, resume, match, answer) and log outcomes (recruiter response, interview, assessment, offer, rejection, withdrawal).
   - Rating data helps user tune config weights, and outcome tracking updates application statuses in the database.
4. **Validation Benchmarking**:
   - Golden datasets evaluate the platform:
     - Matching Precision/Recall Calibration.
     - Resume Factual Integrity (asserting 0 fabricated claims).
     - Screening Answer Grounding (adversarial queries blocked safely).
     - Form Automation Field Mapping and Duplicate URL Prevention.

---

## Phase 16 Flow: Personalization, Feedback Learning & Continuous Optimization

1. **Preference Configuration & Versioning**:
   - `PersonalPreferenceProfile` holds explicit settings and toggles (ON/OFF) for role, company, workplace mode, salary, skill, and location configurations.
   - User updates trigger a snapshot saved to `PreferenceConfigurationVersion` to enable manual rollback.
2. **Behavioral Signal & Feedback Logging**:
   - Explicit user feedback (Save, Skip, Interested, Rejection reason) and behavioral signals are stored in the database.
3. **Smart Matching Personalization**:
   - Scoring engine computes personalized scores by adjusting the base score with a preference multiplier and a job quality warning factor.
4. **Non-Intrusive Inferences & System Suggestions**:
   - `PreferenceInferenceService` maps behavioral trends into suggestions, requiring direct user approval (`Accept`, `Dismiss`, `Remind Later`) to update configurations.
5. **Recommendation Diversification**:
   - Recommenders apply round-robin scheduling across company, role category, source, and location parameters to present a varied list of target jobs.
