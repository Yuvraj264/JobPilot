# JobPilot Architecture & Design Patterns

## Overview
JobPilot is designed as a modular, event-driven, and adapter-based platform for assisting job seekers in finding and applying to relevant job positions safely.

## High-Level Component Structure

```
                  ┌──────────────────────┐
                  │    React Frontend    │
                  └──────────┬───────────┘
                             │ REST API
                  ┌──────────▼───────────┐
                  │   FastAPI Backend    │
                  └────┬─────┬──────┬────┘
                       │     │      │
          ┌────────────┘     │      └────────────┐
          ▼                  ▼                   ▼
┌──────────────────┐ ┌───────────────┐ ┌──────────────────┐
│ PostgreSQL (ORM) │ │ AI & Matching │ │  Browser Agent   │
└──────────────────┘ └───────────────┘ └─────────┬────────┘
                                                 │
                                       ┌─────────▼────────┐
                                       │ Playwright Engine│
                                       └──────────────────┘
```

## Job Source Adapter Architecture (Anticipated)
Future job platform ingestors must implement the `JobSourceAdapter` interface to ensure clean separation of concerns and maintainability.

```
                  ┌──────────────────────┐
                  │   JobSourceAdapter   │
                  └──────────┬───────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌────────────────────┐
│LinkedInAdapter│     │ IndeedAdapter│      │CompanyCareerAdapter│
└──────────────┘      └──────────────┘      └────────────────────┘
```

## Human-in-the-Loop Workflow
Application submissions will be gated by explicit human approval steps. Automated interactions pause at review points to present generated answers and tailored materials to the user for verification.
