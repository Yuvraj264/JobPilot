# Agent Safety Policy & Action Gateway

The safety of autonomous operations is enforced by a layered policy engine that overrides AI reasoning.

## Policy Precedence Hierarchy

1. **Global Safety**: Checks domain allowlist filters and anti-bot intervention.
2. **Account Policy**: Enforces daily application limits across all missions.
3. **Mission Policy**: Tracks campaign budgets.
4. **Job Policy**: Ensures human approval check status and valid submission authorization.

## Prompt Injection Protections

The decision engine scans target job details and rejects instructions containing hostile directives (e.g. "ignore safety rules").
