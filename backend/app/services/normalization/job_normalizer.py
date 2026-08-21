import re
from datetime import datetime
from typing import Dict, Any, Optional
from app.services.normalization.location_normalizer import LocationNormalizer
from app.services.normalization.employment_type_normalizer import EmploymentTypeNormalizer
from app.services.normalization.workplace_type_normalizer import WorkplaceTypeNormalizer


class JobNormalizer:
    """
    Main Job Normalizer engine converting heterogeneous raw source dictionaries into the common Job schema.
    """

    @staticmethod
    def normalize_raw_job(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes a raw job dictionary into standard fields.
        Raises ValueError if mandatory fields (title, company) are missing.
        """
        raw_title = raw_data.get("title") or raw_data.get("raw_title")
        raw_company = raw_data.get("company") or raw_data.get("raw_company")

        if not raw_title or not str(raw_title).strip():
            raise ValueError("Malformed raw job payload: missing job title.")
        if not raw_company or not str(raw_company).strip():
            raise ValueError("Malformed raw job payload: missing company name.")

        title = re.sub(r"\s+", " ", str(raw_title).strip())
        company_name = re.sub(r"\s+", " ", str(raw_company).strip())

        # Normalize Location
        raw_loc = raw_data.get("location") or raw_data.get("raw_location")
        clean_loc, std_loc = LocationNormalizer.normalize(raw_loc)

        # Normalize Employment & Workplace Types
        raw_emp = raw_data.get("employment_type") or raw_data.get("raw_employment_type")
        employment_type = EmploymentTypeNormalizer.normalize(raw_emp)

        raw_workplace = raw_data.get("workplace_type") or raw_data.get("raw_workplace_type")
        workplace_type = WorkplaceTypeNormalizer.normalize(raw_workplace)

        # If workplace type was unknown, check location text for 'remote' or 'hybrid'
        if workplace_type == "UNKNOWN" and clean_loc:
            workplace_type = WorkplaceTypeNormalizer.normalize(clean_loc)

        # Salary & Experience numeric bounds
        salary_min = JobNormalizer._parse_float(raw_data.get("salary_min"))
        salary_max = JobNormalizer._parse_float(raw_data.get("salary_max"))
        salary_currency = str(raw_data.get("salary_currency") or "USD").upper()

        exp_min = JobNormalizer._parse_float(raw_data.get("experience_min"))
        exp_max = JobNormalizer._parse_float(raw_data.get("experience_max"))

        # URLs
        job_url = JobNormalizer._clean_url(raw_data.get("job_url") or raw_data.get("raw_url"))
        company_url = JobNormalizer._clean_url(raw_data.get("company_url"))
        application_url = JobNormalizer._clean_url(raw_data.get("application_url") or job_url)

        # Description
        description = raw_data.get("description") or raw_data.get("raw_description") or ""

        # Parse posted_at date if provided
        posted_at = JobNormalizer._parse_datetime(raw_data.get("posted_at"))

        return {
            "external_job_id": raw_data.get("external_id") or raw_data.get("external_job_id"),
            "title": title,
            "company_name": company_name,
            "company_url": company_url,
            "job_url": job_url,
            "location": clean_loc,
            "normalized_location": std_loc,
            "description": description.strip() if description else None,
            "employment_type": employment_type,
            "workplace_type": workplace_type,
            "experience_min": exp_min,
            "experience_max": exp_max,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency,
            "posted_at": posted_at,
            "application_url": application_url,
            "source_metadata": raw_data.get("metadata", {}),
            "status": "DISCOVERED",
        }

    @staticmethod
    def _parse_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_url(url: Any) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None
        cleaned = url.strip()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned
        return None

    @staticmethod
    def _parse_datetime(val: Any) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                pass
        return None
