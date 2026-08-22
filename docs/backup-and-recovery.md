# JobPilot — Backup & Recovery Playbooks

This document outlines standard operational playbooks for database backups, file uploads backup, configuration presets preservation, and emergency recovery verification.

## 1. Backup Strategy

The critical state of JobPilot consists of:
1. **PostgreSQL Database:** User profiles, resumes metadata, matches, tailored resume structures, applications, audit logs, and configurations.
2. **File Storage:** Physical PDF/DOCX resumes (both master and tailored copies), and screenshots from execution verification.

### Database Backup
Use `pg_dump` to create compressed transaction-safe SQL script exports.
* **Cron schedule:** Daily at 02:00 AM.
* **Command:**
  ```bash
  pg_dump -h localhost -p 5433 -U jobpilot -d jobpilot_db -F c -b -v -f /backups/db/jobpilot_$(date +%F).dump
  ```

### File Storage Backup
Create timestamped tarballs of the `./storage/` directories.
* **Cron schedule:** Daily at 02:30 AM.
* **Command:**
  ```bash
  tar -czf /backups/files/storage_$(date +%F).tar.gz ./storage/
  ```

---

## 2. Restore Procedure

### Database Restore
In case of database loss or migration to new hardware:
1. Re-initialize database:
   ```bash
   dropdb -h localhost -p 5433 -U postgres jobpilot_db
   createdb -h localhost -p 5433 -U postgres jobpilot_db
   ```
2. Restore schema and data from dump:
   ```bash
   pg_restore -h localhost -p 5433 -U postgres -d jobpilot_db -v /backups/db/jobpilot_TARGET_DATE.dump
   ```
3. Run any outstanding migrations:
   ```bash
   PYTHONPATH=backend alembic upgrade head
   ```

### File Storage Restore
Extract files directly back to target locations:
```bash
tar -xzf /backups/files/storage_TARGET_DATE.tar.gz -C ./
```

---

## 3. Disaster Recovery Test Scenario

To verify backup validity:
1. Stop backend application.
2. Backup active DB and files: `pg_dump` + `tar`.
3. Drop DB and delete `./storage/` directory.
4. Execute Restore Procedure commands.
5. Boot backend and verify profiles, resumes, matches, applications, and audit logs remain consistent.
