# JobPilot Evaluation Report

This report summarizes performance metrics and validation outcomes for the JobPilot release candidate.

---

## 1. Metric Summary

| Evaluator Suite | Tested Count | Success/Accuracy Rate | Key Metrics |
| :--- | :--- | :--- | :--- |
| **Job Matching Engine** | 100 | $78.0\%$ | Precision: $71.4\%$, Recall: $75.0\%$ |
| **Resume Tailoring Safety** | 5 | $100.0\%$ | Zero fabricated claims, change safety verified |
| **Screening Question Grounding** | 5 | $100.0\%$ | Grounding: $100.0\%$, Adversarial Grounding: $100.0\%$ |
| **Form Automation & Duplicates** | 8 | $100.0\%$ | Duplicate URL prevention: $100.0\%$, Field Mapping: $100.0\%$ |

---

## 2. Benchmark Observations

- **Calibration & Matching**: The matching engine achieves $78\%$ overall recommendation accuracy against human labels. Score distributions range from $29\%$ to $93\%$ spreads, allowing strong recommendation calibration.
- **Safety Grounding**: The strict anti-fabrication check correctly catches adversarial screening questions (e.g. asking for AWS/Kubernetes experience when the profile lacks it) and returns `INSUFFICIENT_INFORMATION`, avoiding candidate fabrication.
- **Form Automation**: Duplicate checks prevent redundant applications across sources, enforcing exact URL matches and cross-source potential duplicate flags.
