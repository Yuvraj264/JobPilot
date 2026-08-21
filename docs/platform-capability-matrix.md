# Platform Capability Matrix

This document provides a comprehensive review of official API availability, public access terms, and automation policies for primary job platforms and career portals. All details have been verified as of August 22, 2026.

## Matrix

| Platform | Job Discovery | Official API | Public Pages | Browser Automation | Application Automation | Authentication | Current Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | LIMITED | NOT AVAILABLE | LIMITED | NOT AVAILABLE | NOT AVAILABLE | REQUIRED | HUMAN_ASSISTED |
| **Indeed** | LIMITED | NOT AVAILABLE | LIMITED | NOT AVAILABLE | NOT AVAILABLE | NOT REQUIRED (Search) | HUMAN_ASSISTED |
| **Company Career Pages** | SUPPORTED | LIMITED | SUPPORTED | SUPPORTED | NOT AVAILABLE | NOT REQUIRED | SUPPORTED |
| **Greenhouse (ATS)** | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT AVAILABLE | NOT REQUIRED (Get) | SUPPORTED |
| **Lever (ATS)** | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT AVAILABLE | NOT REQUIRED (Get) | SUPPORTED |
| **USAJobs** | SUPPORTED | SUPPORTED | SUPPORTED | NOT AVAILABLE | NOT AVAILABLE | REQUIRED (API Key) | SUPPORTED |

---

## Detailed Platform Analysis

### 1. LinkedIn
* **Job Discovery:** LIMITED (No public job search API. Standard access requires applying to LinkedIn Talent Solutions partner programs).
* **Official API:** NOT AVAILABLE for general developer job-search / ingestion. Only partner APIs exist for job posting.
* **Public Pages:** LIMITED (Publicly accessible search result page exists, but is aggressively rate-limited and protected by CAPTCHAs/anti-bot systems).
* **Browser Automation:** NOT AVAILABLE (Prohibited under LinkedIn's User Agreement, Section 8.2).
* **Application Automation:** NOT AVAILABLE (Prohibited and technically blocked).
* **Authentication:** REQUIRED for personalized or deep search; public pages require no login initially but block rapid traffic.
* **Implementation Decision:** Mark adapter as `UNAVAILABLE` for automated discovery. Expose capability metadata denoting that LinkedIn requires human assistance (`requires_human=True`, `application_automation=False`). If triggered, raise a standard `UNSUPPORTED_OPERATION` or `AUTHENTICATION_REQUIRED` exception.
* **Source & Date Verified:** [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement) - August 22, 2026.

### 2. Indeed
* **Job Discovery:** LIMITED (Publisher API is deprecated and retired for new developers. Partner registrations are highly restricted and selective).
* **Official API:** NOT AVAILABLE (Deprecated XML feeds and search endpoints are no longer accessible without enterprise partnerships).
* **Public Pages:** LIMITED (Public listings exist but are behind Cloudflare/anti-bot protection layers).
* **Browser Automation:** NOT AVAILABLE (Prohibited by Indeed's Terms of Service; automated scraping is actively blocked).
* **Application Automation:** NOT AVAILABLE (Indeed Apply is only accessible to integrated ATS partners).
* **Authentication:** NOT REQUIRED for basic search web pages, but anti-bot measures enforce interactive challenges.
* **Implementation Decision:** Mark adapter as `UNAVAILABLE` for fully automated discovery. Expose metadata indicating `application_automation=False` and return explicit status codes.
* **Source & Date Verified:** [Indeed Developer Portal](https://developer.indeed.com/) - August 22, 2026.

### 3. Company Career Pages (Generic)
* **Job Discovery:** SUPPORTED (Publicly crawlable HTML portals).
* **Official API:** LIMITED (Varies by host company, but public ATS feeds are often readable).
* **Public Pages:** SUPPORTED (Directly viewable by public web browsers and scrapers).
* **Browser Automation:** SUPPORTED (Usually permitted, provided standard rate limits and robots.txt rules are respected).
* **Application Automation:** NOT AVAILABLE (Applying is not automated directly in this phase).
* **Authentication:** NOT REQUIRED.
* **Implementation Decision:** Implement a fully configurable `CompanyCareersJobSourceAdapter` using deterministic DOM CSS selectors, structured JSON-LD parsing, and automated pagination.
* **Source & Date Verified:** General Web Standards - August 22, 2026.

### 4. Greenhouse (ATS)
* **Job Discovery:** SUPPORTED (Provides a public, unauthenticated Job Board API).
* **Official API:** SUPPORTED (`GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs` returns a JSON list of all open positions).
* **Public Pages:** SUPPORTED.
* **Browser Automation:** SUPPORTED (Direct API fetching is preferred over visual selectors).
* **Application Automation:** NOT AVAILABLE (HTTP Basic Auth/API Key is required for POST submissions, which is not supported in this phase).
* **Authentication:** NOT REQUIRED for listing jobs.
* **Implementation Decision:** Support fetching Greenhouse job listings natively inside the generic `CompanyCareersJobSourceAdapter`.
* **Source & Date Verified:** [Greenhouse Job Board API Documentation](https://developers.greenhouse.io/) - August 22, 2026.

### 5. Lever (ATS)
* **Job Discovery:** SUPPORTED (Provides a public, unauthenticated Postings API).
* **Official API:** SUPPORTED (`GET https://api.lever.co/v0/postings/{company}` returns structured JSON data).
* **Public Pages:** SUPPORTED.
* **Browser Automation:** SUPPORTED (Direct API ingestion is preferred).
* **Application Automation:** NOT AVAILABLE.
* **Authentication:** NOT REQUIRED for job retrieval.
* **Implementation Decision:** Integrate direct Lever JSON endpoints into the `CompanyCareersJobSourceAdapter` parser configuration.
* **Source & Date Verified:** [Lever Postings API Documentation](https://hire.lever.co/developer/postings) - August 22, 2026.

### 6. USAJobs
* **Job Discovery:** SUPPORTED (Provides a fully documented REST search API).
* **Official API:** SUPPORTED (`GET https://data.usajobs.gov/api/Search`).
* **Public Pages:** SUPPORTED.
* **Browser Automation:** NOT AVAILABLE (API key is required, and automated UI scraping is blocked/prohibited).
* **Application Automation:** NOT AVAILABLE (Application occurs on agency-specific websites).
* **Authentication:** REQUIRED (Must request a developer API Key and pass it in the `Authorization-Key` header, along with `User-Agent`).
* **Implementation Decision:** Treat USAJobs as a structured API-based adapter. Since it requires authentication (Developer API Key), mock/prepare the request structure, verify key presence via environment variables, and return `AUTHENTICATION_REQUIRED` if the key is missing.
* **Source & Date Verified:** [USAJOBS Developer Portal](https://developer.usajobs.gov/) - August 22, 2026.
