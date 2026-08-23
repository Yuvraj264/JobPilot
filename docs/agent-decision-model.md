# Agent Decision Model

The Agent Decision Model represents the state transition planning step of JobPilot.

## Decisions Vocabulary

- **DISCOVER**: Trigger job ingestion.
- **SKIP**: Job does not fit campaign bounds.
- **SAVE**: Bookmarks job without action.
- **REVIEW**: Flag for manual approval review.
- **PREPARE**: Build package and resume tailoring.
- **WAIT**: Halted on human approval or captcha validation.
- **QUEUE**: Insert application to submission queue.
- **EXECUTE**: Submit permitting applications.
- **RETRY**: Resubmit transient failed jobs.
- **STOP**: Immediate campaign termination.
