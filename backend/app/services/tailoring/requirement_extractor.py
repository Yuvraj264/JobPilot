import json
from typing import List, Dict, Any
from app.models.job import Job


class RequirementCategory:
    TECHNICAL_SKILL = "TECHNICAL_SKILL"
    TOOL = "TOOL"
    FRAMEWORK = "FRAMEWORK"
    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    DATABASE = "DATABASE"
    TESTING_TECHNOLOGY = "TESTING_TECHNOLOGY"
    CLOUD_TECHNOLOGY = "CLOUD_TECHNOLOGY"
    DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE"
    SOFT_SKILL = "SOFT_SKILL"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"
    RESPONSIBILITY = "RESPONSIBILITY"
    ROLE_KEYWORD = "ROLE_KEYWORD"
    OTHER = "OTHER"


class JobRequirementExtractor:
    """
    Job Requirement Extractor parsing normalized Job objects into classified requirement tokens.
    """

    @staticmethod
    def _classify_token(token: str) -> str:
        t = token.lower()
        if t in ["python", "java", "c++", "javascript", "typescript", "c#", "go", "ruby"]:
            return RequirementCategory.PROGRAMMING_LANGUAGE
        if t in ["sql", "postgresql", "postgres", "mongodb", "mysql", "redis"]:
            return RequirementCategory.DATABASE
        if t in ["selenium", "pytest", "cypress", "junit", "testing", "qa", "regression testing"]:
            return RequirementCategory.TESTING_TECHNOLOGY
        if t in ["aws", "docker", "kubernetes", "azure", "gcp"]:
            return RequirementCategory.CLOUD_TECHNOLOGY
        if t in ["git", "jira", "postman", "jenkins"]:
            return RequirementCategory.TOOL
        if t in ["fastapi", "react", "django", "flask", "spring"]:
            return RequirementCategory.FRAMEWORK
        return RequirementCategory.TECHNICAL_SKILL

    @classmethod
    def _parse_skills_list(cls, raw_val: Any) -> List[str]:
        if not raw_val:
            return []
        if isinstance(raw_val, list):
            return [str(x) for x in raw_val]
        if isinstance(raw_val, str):
            try:
                parsed = json.loads(raw_val)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
            return [x.strip() for x in raw_val.split(",") if x.strip()]
        return []

    @classmethod
    def extract_requirements(cls, job: Job) -> List[Dict[str, Any]]:
        reqs = []
        seen = set()

        raw_meta = getattr(job, "source_metadata", {}) or {}
        req_skills = cls._parse_skills_list(getattr(job, "required_skills", None) or raw_meta.get("required_skills"))
        pref_skills = cls._parse_skills_list(getattr(job, "preferred_skills", None) or raw_meta.get("preferred_skills"))

        # 1. Required Skills
        for s in req_skills:
            if s and s.lower() not in seen:
                seen.add(s.lower())
                reqs.append({
                    "name": s,
                    "category": cls._classify_token(s),
                    "importance": "REQUIRED"
                })

        # 2. Preferred Skills
        for s in pref_skills:
            if s and s.lower() not in seen:
                seen.add(s.lower())
                reqs.append({
                    "name": s,
                    "category": cls._classify_token(s),
                    "importance": "PREFERRED"
                })

        # 3. Extract tokens from Title & Description keywords
        title_words = [w.strip(",.()") for w in (job.title or "").split() if len(w) > 2]
        for w in title_words:
            if w.lower() not in seen and w.lower() in ["qa", "engineer", "testing", "developer", "automation"]:
                seen.add(w.lower())
                reqs.append({
                    "name": w,
                    "category": RequirementCategory.ROLE_KEYWORD,
                    "importance": "REQUIRED"
                })

        return reqs
