# JobPilot — Operational Flow

## Overview
JobPilot is an AI-assisted job application automation platform. Its lifecycle flows through 10 completed phases:

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

