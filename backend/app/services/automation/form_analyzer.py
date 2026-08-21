import re
from typing import Dict, Any


class FormAnalyzer:
    """
    Form Analyzer classifying form controls into semantic field types using deterministic heuristics.
    """

    @staticmethod
    def classify_field(el: Dict[str, Any]) -> str:
        tag = el.get("tag_name", "").lower()
        input_type = el.get("input_type", "").lower()
        label = el.get("label", "").lower()
        name = el.get("name", "").lower()
        id_str = el.get("id", "").lower()

        blob = f"{label} {name} {id_str}"

        # 1. File Upload / Resume
        if input_type == "file" or "resume" in blob or "cv" in blob:
            return "RESUME"

        # 2. Textarea / Screening Questions
        if tag == "textarea" or "why" in blob or "describe" in blob or "interest" in blob or "question" in blob:
            return "SCREENING_QUESTION"

        # 3. Email
        if input_type == "email" or "email" in blob:
            return "EMAIL"

        # 4. Phone
        if input_type == "tel" or "phone" in blob or "mobile" in blob or "contact_num" in blob:
            return "PHONE"

        # 5. Personal Name
        if "full name" in blob or "applicant_name" in blob or "first name" in blob or "last name" in blob or "candidate_name" in blob:
            return "PERSONAL_NAME"

        # 6. Education
        if "degree" in blob or "qualification" in blob:
            return "DEGREE"
        if "college" in blob or "university" in blob or "institution" in blob:
            return "INSTITUTION"
        if "graduation" in blob or "grad_year" in blob or "passing_year" in blob:
            return "GRADUATION_YEAR"

        # 7. Professional
        if "years of experience" in blob or "years_exp" in blob or "experience_years" in blob:
            return "EXPERIENCE"
        if "current role" in blob or "job title" in blob or "designation" in blob:
            return "CURRENT_ROLE"
        if "skill" in blob or "technolog" in blob:
            return "SKILLS"

        # 8. Preferences
        if "relocate" in blob or "relocation" in blob:
            return "RELOCATION"
        if "workplace" in blob or "work_arrangement" in blob:
            return "WORKPLACE_TYPE"
        if "salary" in blob or "ctc" in blob or "compensation" in blob:
            return "SALARY"
        if "country" in blob:
            return "COUNTRY"
        if "city" in blob or "location" in blob:
            return "LOCATION"

        return "UNKNOWN"
