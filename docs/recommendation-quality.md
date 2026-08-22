# Recommendation Quality & Diversification

This document details recommendation quality tracking, diversification, and exploration modes in JobPilot.

---

## 1. Recommendation Diversifier

To prevent lists of identical job listings, `RecommendationDiversifier` applies round-robin scheduling across:
- **Company**: Restricts duplicate companies in top recommendation results.
- **Roles**: Diversifies job titles (e.g.SDET, QA Automation, Test Analyst).
- **Location**: Diversifies job cities.

---

## 2. Exploration vs Strict Preference

- **Strict Preference Mode**: Prioritizes known user explicit target roles and skills. Excludes low-matching adjacent listings (overall score < 75.0).
- **Exploration Mode**: Intermittently injects nearby matched titles and adjacent technologies, allowing candidates to discover related roles (minimum score threshold set to 60.0).
