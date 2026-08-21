from typing import Dict, List, Any
from app.models.resume import Resume


class QualityService:
    """
    Deterministic Resume Quality Analyzer.
    Evaluates resume section presence, text readability, and formatting completeness.
    """

    @staticmethod
    def analyze_quality(resume: Resume) -> Dict[str, Any]:
        if not resume:
            return {"score": 0, "issues": ["Resume record not found."]}

        score = 0
        issues: List[str] = []

        # 1. Processing Status Check
        if resume.processing_status != "PROCESSED":
            return {
                "score": 0,
                "issues": [f"Resume is currently in '{resume.processing_status}' state. Run processing first."]
            }

        # 2. File Size & Type Readability (15 points)
        if resume.file_size and resume.file_size > 1024:
            score += 15
        else:
            issues.append("Resume file size is unusually small.")

        # 3. Skills Section (25 points)
        skill_count = len(resume.skills) if resume.skills else 0
        if skill_count >= 5:
            score += 25
        elif skill_count > 0:
            score += int((skill_count / 5) * 25)
            issues.append(f"Only {skill_count} skills extracted. Consider listing additional core technical skills.")
        else:
            issues.append("No technical or professional skills were detected in this resume.")

        # 4. Education Section (20 points)
        if resume.education and len(resume.education) > 0:
            score += 20
        else:
            issues.append("No educational qualifications were detected.")

        # 5. Work Experience / Projects Section (25 points)
        exp_count = len(resume.experiences) if resume.experiences else 0
        proj_count = len(resume.projects) if resume.projects else 0
        if exp_count > 0 or proj_count > 0:
            score += 25
        else:
            issues.append("Neither work experience nor project portfolios were detected.")

        # 6. Certifications Bonus (15 points)
        if resume.certifications and len(resume.certifications) > 0:
            score += 15
        else:
            issues.append("No professional certifications detected.")

        final_score = max(0, min(100, score))
        return {
            "score": final_score,
            "issues": issues,
            "skills_detected": skill_count,
            "education_entries": len(resume.education) if resume.education else 0,
            "experience_entries": exp_count,
            "project_entries": proj_count,
            "certification_entries": len(resume.certifications) if resume.certifications else 0,
        }
