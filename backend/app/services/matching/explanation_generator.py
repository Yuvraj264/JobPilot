from typing import Dict, List, Any


class ExplanationGenerator:
    """
    Deterministic Explanation Generator.
    Produces human-readable summary, strengths, and concerns from evaluation facts.
    """

    @staticmethod
    def generate(
        job_title: str,
        company_name: str,
        overall_score: float,
        recommendation: str,
        eligible: bool,
        hard_failures: List[str],
        skill_res: Dict[str, Any],
        role_res: Dict[str, Any],
        loc_res: Dict[str, Any],
        exp_res: Dict[str, Any],
        salary_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        strengths: List[str] = []
        concerns: List[str] = []

        # Skills
        matched = skill_res.get("matched_skills", [])
        if matched:
            strengths.append(f"Matched core skills: {', '.join(matched[:5])}")
        missing_req = skill_res.get("missing_required", [])
        if missing_req:
            concerns.append(f"Missing required skills: {', '.join(missing_req[:5])}")
        missing_pref = skill_res.get("missing_preferred", [])
        if missing_pref:
            concerns.append(f"Missing preferred skills: {', '.join(missing_pref[:3])}")

        # Role
        if role_res.get("score", 0) >= 80:
            strengths.append(f"Target role matches '{job_title}' ({role_res.get('role_match_type')})")
        elif role_res.get("score", 0) < 60:
            concerns.append(f"Role title '{job_title}' differs significantly from candidate target roles.")

        # Location
        if loc_res.get("score", 0) >= 90:
            strengths.append(loc_res.get("match_reason"))
        elif loc_res.get("score", 0) < 50:
            concerns.append(loc_res.get("match_reason"))

        # Experience
        if exp_res.get("score", 0) >= 90:
            strengths.append(exp_res.get("match_reason"))
        else:
            concerns.append(exp_res.get("match_reason"))

        # Hard failures
        for hf in hard_failures:
            concerns.append(f"HARD FAILURE: {hf}")

        if recommendation == "APPLY":
            summary = f"Strong match ({overall_score:.1f}%) for {job_title} at {company_name}. Recommended to Apply."
        elif recommendation == "REVIEW":
            summary = f"Moderate match ({overall_score:.1f}%) for {job_title} at {company_name}. Requires human review."
        else:
            summary = f"Low suitability or hard constraint failure for {job_title} at {company_name}. Recommended to Skip."

        return {
            "summary": summary,
            "strengths": strengths,
            "concerns": concerns,
        }
