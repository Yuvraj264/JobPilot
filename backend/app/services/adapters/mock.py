import json
import os
from typing import Dict, List, Any, Optional
from app.services.adapters.base import JobSourceAdapter


class MockJobSourceAdapter(JobSourceAdapter):
    """
    Mock Job Source Adapter generating or reading synthetic jobs for development and pipeline testing.
    Adheres strictly to JobSourceAdapter interface.
    """

    def __init__(self, fixture_path: Optional[str] = None):
        self._fixture_path = fixture_path or os.path.join(os.getcwd(), "tests", "fixtures", "jobs.json")
        self._jobs_cache: Optional[List[Dict[str, Any]]] = None

    def source_name(self) -> str:
        return "mock"

    def display_name(self) -> str:
        return "Mock Job Source"

    def source_type(self) -> str:
        return "MANUAL"

    def _load_jobs(self) -> List[Dict[str, Any]]:
        if self._jobs_cache is not None:
            return self._jobs_cache

        if os.path.exists(self._fixture_path):
            try:
                with open(self._fixture_path, "r", encoding="utf-8") as f:
                    self._jobs_cache = json.load(f)
                    return self._jobs_cache
            except Exception as e:
                print(f"Error loading mock fixture from {self._fixture_path}: {e}")

        # Fallback synthetic job array
        self._jobs_cache = [
            {
                "external_id": "MOCK-001",
                "title": "Software Engineer (Python)",
                "company": "Mock Tech Corp",
                "location": "Bangalore, India",
                "description": "Mock synthetic job posting for testing job discovery pipeline.",
                "employment_type": "FULL_TIME",
                "workplace_type": "HYBRID",
                "salary_min": 100000.0,
                "salary_max": 130000.0,
                "salary_currency": "USD",
                "job_url": "https://mocktech.example.com/jobs/001",
                "application_url": "https://mocktech.example.com/apply/001",
            }
        ]
        return self._jobs_cache

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        all_jobs = self._load_jobs()
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        return all_jobs[start_idx:end_idx]

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        all_jobs = self._load_jobs()
        for j in all_jobs:
            if j.get("external_id") == external_id:
                return j
        return None

    def health_check(self) -> bool:
        return True

    def metadata(self) -> Dict[str, Any]:
        meta = super().metadata()
        meta["supported_access_method"] = "Synthetic JSON Fixture"
        meta["notes"] = "Mock adapter generating synthetic job listings for safe local pipeline verification."
        return meta
