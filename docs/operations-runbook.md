# JobPilot — Operations Runbook

This runbook describes mitigation workflows for standard operational errors, infrastructure crashes, rate-limiting locks, and system recovery.

## 1. Database Connection Failures
* **Symptom:** Backend starts and crashes immediately with `DB_CONNECTION_FAILED` logs.
* **Checks:**
  1. Verify PostgreSQL container is running: `docker ps | grep postgres`.
  2. Verify DB host/port parameters in `.env`.
* **Fix:** Restart Postgres container or update the target `DATABASE_URL`.

## 2. Scraping Rate Limits & Failures
* **Symptom:** Discovery run status is `PARTIAL` or `FAILED` with `RATE_LIMITED` error codes.
* **Checks:**
  * View backend logs to identify which adapter generated the warning.
* **Fix:** Increase delays or decrease maximum pages limits configuration under the Source settings in the dashboard.

## 3. Orphaned Browser Processes & Crashes
* **Symptom:** Disk space depletion or memory leaks due to lingering Chromium processes.
* **Checks:**
  * List chromium processes: `ps aux | grep -i chromium`.
* **Fix:** Kill lingering processes: `pkill -f chromium`. The execution worker has been hardened with strict `try...finally` wrappers to prevent this.

## 4. Stuck Applications & Interrupted Submissions
* **Symptom:** Active submissions showing in `SUBMITTING` or `RUNNING` status indefinitely.
* **Checks:**
  * Find worker heartbeat status in `/health/scheduler`.
* **Fix:** Transition stuck entries on startup:
  - RUNNING discovery runs → `FAILED`.
  - SUBMITTING applications → `SUBMISSION_UNVERIFIED`.
  This is executed automatically by the orchestrator recovery engine.

## 5. Storage / Disk Full Conditions
* **Symptom:** File uploads fail with `FILE_UPLOAD_FAILED` logs.
* **Checks:**
  * Verify filesystem disk bounds: `df -h`.
* **Fix:** Run prune scripts for screenshots and cache files.
  ```bash
  find ./storage/screenshots -type f -mtime +14 -delete
  ```
