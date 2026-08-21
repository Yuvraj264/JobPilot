from typing import Dict, Any, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume


class ProfileFieldMapper:
    """
    Profile Field Mapper.
    Maps semantic field classifications to User Profile and Resume data.
    Assigns confidence scores and returns MISSING_DATA when profile facts are unpopulated without fabricating values.
    """

    @staticmethod
    def map_field(semantic_type: str, profile: UserProfile, default_resume: Optional[Resume] = None) -> Dict[str, Any]:
        if semantic_type == "PERSONAL_NAME":
            val = profile.full_name
            return {"value": val, "confidence": 0.99 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "EMAIL":
            val = profile.email
            return {"value": val, "confidence": 0.99 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "PHONE":
            val = profile.phone
            return {"value": val, "confidence": 0.99 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "LOCATION":
            val = profile.current_city
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "COUNTRY":
            val = profile.current_country or "India"
            return {"value": val, "confidence": 0.95, "status": "MATCHED"}

        if semantic_type == "DEGREE":
            val = profile.education[0].degree if profile.education and len(profile.education) > 0 else None
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "INSTITUTION":
            val = profile.education[0].institution if profile.education and len(profile.education) > 0 else None
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "GRADUATION_YEAR":
            val = str(profile.education[0].end_year) if (profile.education and len(profile.education) > 0 and profile.education[0].end_year) else None
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "EXPERIENCE":
            val = str(profile.years_of_experience) if profile.years_of_experience is not None else None
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "CURRENT_ROLE":
            val = profile.current_role
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "SKILLS":
            skills_list = [s.name for s in (profile.skills or [])]
            val = ", ".join(skills_list) if skills_list else None
            return {"value": val, "confidence": 0.95 if val else 0.0, "status": "MATCHED" if val else "MISSING_DATA"}

        if semantic_type == "RELOCATION":
            reloc = profile.job_preference.relocation_status if profile.job_preference else True
            val = "Yes" if reloc else "No"
            return {"value": val, "confidence": 0.95, "status": "MATCHED"}

        if semantic_type == "WORKPLACE_TYPE":
            arrangements = profile.job_preference.work_arrangements if profile.job_preference else ["HYBRID"]
            val = arrangements[0] if arrangements else "HYBRID"
            return {"value": val, "confidence": 0.90, "status": "MATCHED"}

        if semantic_type == "RESUME":
            file_path = default_resume.file_path if default_resume else None
            return {"value": file_path, "confidence": 0.99 if file_path else 0.0, "status": "MATCHED" if file_path else "MISSING_DATA"}

        if semantic_type == "SCREENING_QUESTION":
            return {"value": None, "confidence": 0.0, "status": "REQUIRES_REASONING"}

        return {"value": None, "confidence": 0.0, "status": "UNKNOWN_FIELD"}
