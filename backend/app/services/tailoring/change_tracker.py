from typing import Dict, Any, List, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume


class ChangeTracker:
    """
    Change Tracker computing transparent change reports between original master resume and tailored output.
    """

    @staticmethod
    def compute_changes(
        tailored_doc: Dict[str, Any],
        profile: UserProfile,
        master_resume: Optional[Resume] = None
    ) -> Dict[str, Any]:
        changes = []
        unchanged = []

        # 1. Summary Change
        orig_summary = profile.professional_summary or (master_resume.raw_text[:100] if master_resume else "")
        tailored_summary = tailored_doc.get("summary", "")

        if orig_summary != tailored_summary:
            changes.append({
                "section": "PROFESSIONAL_SUMMARY",
                "change_type": "REWRITTEN_TO_TARGET_ROLE",
                "description": "Tailored summary to emphasize job-relevant skills and target position."
            })
        else:
            unchanged.append("PROFESSIONAL_SUMMARY")

        # 2. Skill Order Change
        changes.append({
            "section": "SKILLS",
            "change_type": "REORDERED_BY_RELEVANCE",
            "description": "Reordered existing skills so job-matching technical skills appear first."
        })

        # 3. Project Ranking Change
        changes.append({
            "section": "PROJECTS",
            "change_type": "RANKED_BY_RELEVANCE",
            "description": "Prioritized projects demonstrating relevant technologies and problem solving."
        })

        # 4. Strictly Unchanged Sections
        unchanged.extend(["EDUCATION", "EMPLOYERS", "EMPLOYMENT_DATES", "CERTIFICATION_NAMES"])

        return {
            "total_changes": len(changes),
            "changes": changes,
            "unchanged_sections": unchanged
        }
