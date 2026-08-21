import pytest
from unittest.mock import patch, MagicMock
from app.services.adapters.linkedin import LinkedInJobSourceAdapter
from app.services.adapters.indeed import IndeedJobSourceAdapter
from app.services.adapters.company_careers import CompanyCareersJobSourceAdapter
from app.services.adapters.base import UnsupportedOperationError


def test_linkedin_adapter_contract():
    adapter = LinkedInJobSourceAdapter()
    assert adapter.source_name() == "linkedin"
    assert adapter.display_name() == "LinkedIn Job Platform"
    assert adapter.health_check() == "unsupported"
    
    metadata = adapter.metadata()
    assert metadata["requires_authentication"] is True
    assert metadata["requires_human_interaction"] is True
    assert metadata["capabilities"]["HUMAN_ASSISTED"] is True
    assert metadata["capabilities"]["DISCOVERY"] is False
    
    with pytest.raises(UnsupportedOperationError):
        adapter.discover_jobs()


def test_indeed_adapter_contract():
    adapter = IndeedJobSourceAdapter()
    assert adapter.source_name() == "indeed"
    assert adapter.display_name() == "Indeed Job Platform"
    assert adapter.health_check() == "unsupported"
    
    metadata = adapter.metadata()
    assert metadata["capabilities"]["DISCOVERY"] is False
    
    with pytest.raises(UnsupportedOperationError):
        adapter.discover_jobs()


@patch("httpx.get")
def test_company_careers_greenhouse_api(mock_get):
    # Mock Greenhouse API response
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "jobs": [
            {
                "id": 12345,
                "title": "Software Engineer",
                "content": "Description content of the job board posting.",
                "absolute_url": "https://boards.greenhouse.io/stripe/jobs/12345",
                "location": {"name": "Seattle, WA"}
            }
        ]
    }
    mock_get.return_value = mock_res
    
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "Stripe",
        "careers_url": "https://boards.greenhouse.io/stripe",
        "discovery_method": "GREENHOUSE_API",
        "board_token": "stripe"
    }
    
    # Invoke single company discovery
    jobs = adapter._discover_single_company(config, limit=10, page=1)
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["company"] == "Stripe"
    assert "greenhouse-12345" in jobs[0]["external_id"]
    assert jobs[0]["location"] == "Seattle, WA"


@patch("httpx.get")
def test_company_careers_lever_api(mock_get):
    # Mock Lever API response
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = [
        {
            "id": "abc-123",
            "text": "Fullstack Developer",
            "descriptionPlain": "Fullstack development on React and Node.",
            "hostedUrl": "https://jobs.lever.co/acme/abc-123",
            "categories": {
                "location": "Toronto, Canada",
                "commitment": "FULL_TIME"
            }
        }
    ]
    mock_get.return_value = mock_res
    
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "Acme",
        "careers_url": "https://jobs.lever.co/acme",
        "discovery_method": "LEVER_API",
        "company_id": "acme"
    }
    
    jobs = adapter._discover_single_company(config, limit=10, page=1)
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Fullstack Developer"
    assert jobs[0]["location"] == "Toronto, Canada"
    assert jobs[0]["employment_type"] == "FULL_TIME"


@patch("httpx.get")
def test_company_careers_json_ld(mock_get):
    # Mock Site B: JSON-LD Career Portal
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "JobPosting",
                "title": "Backend Python Developer",
                "description": "Django and FastAPI developer posting description.",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Innovate Ltd"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "London"
                    }
                },
                "identifier": {
                    "@type": "PropertyValue",
                    "value": "INV-201"
                }
            }
            </script>
        </head>
    </html>
    """
    mock_get.return_value = mock_res
    
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "Innovate Ltd",
        "careers_url": "http://localhost:8000/mock/synthetic-careers/site_b",
        "discovery_method": "JSON_LD"
    }
    
    jobs = adapter._discover_single_company(config, limit=10, page=1)
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Python Developer"
    assert jobs[0]["company"] == "Innovate Ltd"
    assert jobs[0]["location"] == "London"
    assert jobs[0]["external_id"] == "INV-201"


def test_company_careers_site_a_live():
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "TechCorp A",
        "careers_url": "http://localhost:8000/mock/synthetic-careers/site_a",
        "discovery_method": "DOM_SELECTORS",
        "parser_configuration": {
            "job_card_selector": ".job-card",
            "job_link_selector": "a.job-link",
            "job_title_selector": ".job-title",
            "company_selector": ".job-company",
            "location_selector": ".job-location",
            "description_selector": ".job-description",
            "salary_selector": ".job-salary",
            "experience_selector": ".job-experience",
            "next_page_selector": "a.next-page",
            "delay_between_requests": 0.05
        }
    }
    
    # Discovery page 1
    jobs = adapter._discover_single_company(config, limit=2, page=1)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Frontend Engineer"
    assert jobs[0]["company"] == "TechCorp A"
    assert jobs[0]["location"] == "Remote, US"
    assert "React development" in jobs[0]["description"]
    assert jobs[0]["salary_min"] == 120000.0
    
    # Discovery page 2 (via next page selector traversal)
    jobs_p2 = adapter._discover_single_company(config, limit=2, page=2)
    assert len(jobs_p2) == 1
    assert jobs_p2[0]["title"] == "DevOps Engineer"
    assert jobs_p2[0]["location"] == "Austin, TX"


def test_company_careers_site_b_live():
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "Innovate Ltd",
        "careers_url": "http://localhost:8000/mock/synthetic-careers/site_b",
        "discovery_method": "JSON_LD"
    }
    
    jobs = adapter._discover_single_company(config, limit=10, page=1)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Backend Developer"
    assert jobs[0]["company"] == "Innovate Ltd"
    assert jobs[0]["location"] == "London"
    assert jobs[0]["external_id"] == "INV-201"
    
    assert jobs[1]["title"] == "Data Engineer"
    assert jobs[1]["external_id"] == "INV-202"


def test_company_careers_site_c_live():
    adapter = CompanyCareersJobSourceAdapter()
    config = {
        "company_name": "CloudSys",
        "careers_url": "http://localhost:8000/mock/synthetic-careers/site_c",
        "discovery_method": "DOM_SELECTORS",
        "parser_configuration": {
            "job_card_selector": ".job-item",
            "job_link_selector": "a.link-class",
            "job_title_selector": ".title-class",
            "company_selector": ".company-class",
            "location_selector": ".loc-class",
            "description_selector": ".desc-class",
            "salary_selector": ".salary-class",
            "next_page_selector": ".load-more-btn",
            "delay_between_requests": 0.05
        }
    }
    
    jobs = adapter._discover_single_company(config, limit=2, page=1)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Cloud Architect"
    assert jobs[0]["company"] == "CloudSys"
    assert jobs[0]["location"] == "San Francisco, CA"
    assert "AWS architecture" in jobs[0]["description"]
    assert jobs[0]["salary_min"] == 180000.0

