# JobPilot Real-World Validation Plan

This validation plan outlines the testing strategies to verify JobPilot's autonomous and human-assisted components under realistic operating conditions.

---

## 1. Controlled Validation Environments

To measure safety, reliability, and precision, JobPilot validates pipelines across three distinct staging layers:

| Environment | Scope & Intent | Target Population | Safety Limits |
| :--- | :--- | :--- | :--- |
| **Demo Mode** | Synthetic sandboxed execution to demonstrate pipelines without external service dependencies. | Sandbox user ID `99999` | `dry_run = true`, `real_submission = false` |
| **Synthetic Benchmarks** | Golden dataset evaluations measuring matching precision/recall, tailoring grounding, and answer accuracy. | Automated golden dataset profiles | Evaluated locally using metric engines, zero external network traffic |
| **Real Pilot Run** | Controlled application execution on real platforms under direct user authorization. | Whitelisted pilot user profile | Human-in-the-loop review mandatory for all submissions |

---

## 2. Validation Metrics & Targets

We assess system quality using key metrics in four categories:

1. **Matching Precision & Calibration**: Ensure high scores reflect high alignment without missing eligibility.
2. **Resume Factual Integrity**: Enforce zero fabrication (100% factual accuracy).
3. **Screening Grounding**: Ensure AI only answers with verifiable facts, resorting to `INSUFFICIENT_INFORMATION` for adversarial queries.
4. **Execution Reliability**: Track form-filling accuracy and browser recovery rates.
