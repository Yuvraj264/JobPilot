# JobPilot Reliability Targets

This document establishes targeted service levels (SLAs), auto-intervention limits, and browser recovery rates for JobPilot automation pipelines.

---

## 1. Automated Execution Targets

| Metric | Target SLA | Auto-Intervention Threshold | Recovery Action |
| :--- | :--- | :--- | :--- |
| **Form Field Mapping** | $\ge 95\%$ accuracy | Unknown field type detected | Pause execution, trigger `HumanInterventionEvent` |
| **Error Recovery Rate** | $\ge 90\%$ | 3 consecutive transient navigation errors | Reload page, clear cookies, retry with delay |
| **Duplicate Prevention** | $100.0\%$ | Duplicate URL or Ext ID matched | Block run immediately with `IDEMPOTENCY_CONSTRAINT` |
| **Sponsorship Screening** | $100.0\%$ | Ambiguous visa question | Pause execution, request immediate human answer |

---

## 2. Safety Escalation Matrix

1. **Unknown Field Detection**: Pauses automation and notifies user via a top attention-required banner.
2. **Captcha Challenge**: Halts execution, updates run status to `PAUSED`, and prompts manual resolution in the browser.
3. **Session Timeout**: Triggers automated credential check, prompts user to re-authenticate if token invalid.
