from typing import Dict, Any, List, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.tailoring.evidence_selector import EvidenceSelector, EvidenceStrength


class ResumeKeywordAnalyzer:
    """
    Resume Keyword Analyzer measuring matched, missing, and unsupported keywords.
    Computes explanatory ResumeRelevanceScore.
    """

    @staticmethod
    def analyze_keywords(
        requirements: List[Dict[str, Any]],
        profile: UserProfile,
        resume: Optional[Resume] = None
    ) -> Dict[str, Any]:
        matched = []
        unsupported = []

        for req in requirements:
            req_name = req["name"]
            ev = EvidenceSelector.select_evidence_for_requirement(req_name, profile, resume)
            if ev["strength"] in [EvidenceStrength.STRONG, EvidenceStrength.MODERATE]:
                matched.append({
                    "keyword": req_name,
                    "importance": req.get("importance", "REQUIRED"),
                    "strength": ev["strength"],
                    "source": ev["source"]
                })
            else:
                unsupported.append({
                    "keyword": req_name,
                    "importance": req.get("importance", "REQUIRED"),
                    "note": "Unsupported by candidate facts; MUST NOT be fabricated."
                })

        total = len(requirements)
        matched_count = len(matched)
        coverage_pct = round((matched_count / total * 100), 2) if total > 0 else 100.0

        return {
            "total_requirements": total,
            "matched_count": matched_count,
            "unsupported_count": len(unsupported),
            "coverage_percentage": coverage_pct,
            "matched_keywords": matched,
            "unsupported_keywords": unsupported,
        }
