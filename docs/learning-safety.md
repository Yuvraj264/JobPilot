# Learning Safety Policy

JobPilot operates under strict safety policies to prevent AI hallucinations, configuration pollution, and unauthorized updates.

---

## 1. Safety Rules

1. **Direct User Overrides**: Explicit preferences always override inferred preferences.
2. **Confidence Evidence Thresholds**: System suggestions are never generated from single actions; multiple signals must be logged to assert confidence.
3. **Traceability**: All configuration changes are snapshot-versioned and support immediate rollback.
4. **No Automated Inferences**:
   - The system **NEVER** silently updates user profile skills or experience records.
   - Job requirements are never treated as evidence that the user possesses a skill.
   - Resume facts are never modified automatically.
5. **Human-in-the-Loop**: Optimization suggestions require explicit user approval (`[Accept]`) to apply changes.
