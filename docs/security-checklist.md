# JobPilot — Security Checklist

This checklist tracks security auditing guidelines and checks enforced during Phase 13 production hardening.

## [x] 1. Credentials and Secret Management
- [x] All hardcoded tokens, cookies, passwords, and API keys removed from logs, frontend files, and test files.
- [x] `.env.example` and `.env.production.example` contain placeholder values only.
- [x] Database configuration does not use superuser default permissions.

## [x] 2. Authorization Controls
- [x] Authentication logic resolves identity via custom headers (`X-User-Id`).
- [x] All routes check ownership constraints (protecting against IDOR vulnerabilities).
- [x] User B cannot read or edit User A's resumes or applications.

## [x] 3. File & Upload Protections
- [x] Path traversal checks block uploads targeting paths outside `./storage/`.
- [x] Upload sizes restricted to maximum boundaries (default 10MB).
- [x] Strict mime-type verification filters permitted document structures.

## [x] 4. SSRF & allowed Network Bounds
- [x] `URLSecurityService` intercepts outgoing calls and navigations.
- [x] Private IP scopes (RFC 1918), loops (`127.0.0.1`), metadata endpoints (`169.254.169.254`) blocked.
- [x] DNS rebinding protection resolves domain addresses prior to validation.

## [x] 5. Concurrency & Integrity Controls
- [x] Database constraints enforce unique match evaluations and unique applications.
- [x] Atomicity of submission state is guaranteed via row locking (`with_for_update`).
