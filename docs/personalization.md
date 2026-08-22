# Personal Preference Engine Architecture

This document describes how JobPilot personalization works.

---

## 1. Personalization Data Structures

We track user preferences in a dedicated database profile:

- **PersonalPreferenceProfile**: Contains personalization settings, answer writing styles, and preferred/disliked lists for roles, locations, workplace modes, employment types, salary limits, companies, industries, and technologies.
- **PreferenceConfigurationVersion**: Snapshots configuration states to support config history and manual undo rollbacks.
- **BehavioralSignal**: Low-confidence behavioral signals (e.g. opens, view times, edits) that serve as suggestions indicators.

---

## 2. Personalized Match Formula

Personalized matching score is calculated as:
$$\text{overall\_score} = \text{base\_match} \times \text{personalization\_factor} \times \text{job\_quality\_factor}$$

- **base\_match**: Weighted sum of core matching components.
- **personalization\_factor**: Adjustment multiplier calculated from user preferred/disliked roles, skills, and work modes.
- **job\_quality\_factor**: Deductible warning factor (e.g., description incomplete, stale listings).
- **Hard Eligibility**: Personalization matches never override hard eligibility requirements. If a job fails eligibility constraints, matching status is immediately set to `SKIP`.
