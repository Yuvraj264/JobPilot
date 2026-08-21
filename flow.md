# JobPilot — Operational Flow

## Overview
JobPilot is an AI-assisted job application automation platform. Its lifecycle flows through 8 active phases:

```
[Phase 1: Foundation & Infrastructure]
                   │
                   ▼
[Phase 2: User Profile & Preferences Engine]
                   │
                   ▼
[Phase 3: Resume Management & Resume Intelligence]
                   │
                   ▼
[Phase 4: Job Source Architecture & Job Discovery Foundation]
                   │
                   ▼
[Phase 5: Job Matching & Intelligent Job Selection Engine]
                   │
                   ▼
[Phase 6: Mock Application Environment & Agent Foundation]
                   │
                   ▼
[Phase 7: Form Understanding & Screening Question Engine]
                   │
                   ▼
[Phase 8: Resume Tailoring & Application Package Engine]
```

---

## Phase 8 Flow: Resume Tailoring & Application Package Generation

1. **Job Requirement Extraction**:
   - `JobRequirementExtractor` categorizes job tokens into programming languages, databases, cloud, testing tools, and domain keywords.
2. **Evidence Selection & Strength Rating**:
   - `EvidenceSelector` evaluates candidate profile and master resume for factual evidence matching target requirements.
   - Rates evidence strength strictly as `STRONG`, `MODERATE`, `WEAK`, or `NONE`.
3. **Tailoring Plan Generation**:
   - `ResumeTailoringPlan` reorders skills (job matches first) and ranks projects by technology overlap.
4. **Mandatory Truthfulness Validation (Anti-Fabrication)**:
   - `ResumeTruthfulnessValidator` compares candidate content against canonical facts.
   - Rejects generation if unsupported skills (e.g. Cypress), employers, dates, or metrics are introduced.
5. **PDF & DOCX Renderers**:
   - `StandardPDFRenderer` and `StandardDOCXRenderer` produce ATS-scannable document artifacts.
6. **Application Package Assembly**:
   - `ApplicationPackageService` compiles target job, master resume, tailored resume, match score, and screening answers into an `ApplicationPackage` advancing to `READY_FOR_REVIEW`.
