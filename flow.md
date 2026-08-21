# JobPilot — Operational Flow

## Overview
JobPilot is an AI-assisted job application automation platform. Its lifecycle flows through 9 completed phases:

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
