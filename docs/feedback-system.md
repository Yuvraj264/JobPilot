# Controlled Feedback System

JobPilot tracks explicit user feedback to guide recommendation tuning.

---

## 1. Direct Feedback Types

The system supports explicit feedback objects:

- **JobFeedback**: Explicit flags (Interested, Save, Skip, Poor Match, Do not show similar). Allows mapping rejection reasons (mode, location, salary) and liked attributes.
- **ResumeFeedback**: Captures tailoring edits and rating variants.
- **AnswerFeedback**: Tracks user edits on AI-generated question answers to study writing style choices.
- **OutcomeFeedback**: Manual application outcomes (Interview, Offer, Rejection) logged by the user.

---

## 2. Feedback Analytics

Using outcome feedback data, the system builds:
- Skill demand and missing skills gaps metrics.
- Resume variants performance (interview and offer conversion rates).
- Source quality aggregates.
- Interactive companies lists.
