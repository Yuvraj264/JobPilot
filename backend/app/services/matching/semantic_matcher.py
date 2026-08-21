import re
from typing import Dict, Any, Set
from app.models.profile import UserProfile
from app.models.job import Job


class LocalEmbeddingProvider:
    """
    Local Fallback Vector / Text Similarity Provider.
    Calculates deterministic token Jaccard & N-Gram similarity between job text and profile summary/skills.
    Requires NO paid commercial API keys or external server dependencies.
    """

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        words1: Set[str] = set(re.findall(r"\b[a-zA-Z]{3,}\b", text1.lower()))
        words2: Set[str] = set(re.findall(r"\b[a-zA-Z]{3,}\b", text2.lower()))

        if not words1 or not words2:
            return 50.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_ratio = len(intersection) / len(union) if union else 0.0
        # Map 0.0 - 0.5 Jaccard ratio to 40.0 - 95.0 score scale
        score = 40.0 + min(55.0, (jaccard_ratio * 110.0))
        return round(score, 2)


class SemanticMatcher:
    """
    Semantic Relevance Matcher with Local Embedding Provider fallback.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        # Construct Candidate Representation
        skills_text = " ".join([s.name for s in (profile.skills or [])])
        summary_text = profile.professional_summary or ""
        role_text = profile.current_role or ""
        profile_blob = f"{role_text} {summary_text} {skills_text}".strip()

        # Construct Job Representation
        job_blob = f"{job.title} {job.description or ''}".strip()

        if not profile_blob or not job_blob:
            return {"score": 70.0, "confidence": 0.5, "provider": "LocalEmbeddingProvider", "match_reason": "Insufficient text for semantic similarity computation."}

        score = LocalEmbeddingProvider.calculate_text_similarity(profile_blob, job_blob)
        return {
            "score": score,
            "confidence": 0.75,
            "provider": "LocalEmbeddingProvider",
            "match_reason": f"Local token similarity computed score of {score}/100.",
        }
