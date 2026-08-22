import json

# Golden dataset representing profiles, resumes, and synthetic jobs for benchmarks

GOLDEN_PROFILE = {
    "full_name": "Alex Mercer",
    "email": "alex.mercer@example.com",
    "phone": "+1-555-0199",
    "current_city": "San Francisco",
    "current_country": "USA",
    "professional_summary": "Experienced QA Automation Engineer with 5 years designing, building, and maintaining automated testing frameworks using Python, Selenium, and Playwright. Passionate about quality assurance, CI/CD pipelines, and relational database testing.",
    "years_of_experience": 5.0,
    "current_role": "QA Automation Engineer",
    "employment_status": "EMPLOYED",
    "skills": [
        {"name": "Python", "proficiency": "Expert", "years_of_experience": 5.0},
        {"name": "Selenium", "proficiency": "Expert", "years_of_experience": 4.0},
        {"name": "Playwright", "proficiency": "Advanced", "years_of_experience": 2.0},
        {"name": "SQL", "proficiency": "Intermediate", "years_of_experience": 3.0},
        {"name": "Manual Testing", "proficiency": "Intermediate", "years_of_experience": 5.0},
        {"name": "Git", "proficiency": "Advanced", "years_of_experience": 4.0},
        {"name": "Jira", "proficiency": "Intermediate", "years_of_experience": 3.0},
        {"name": "Postman", "proficiency": "Intermediate", "years_of_experience": 2.0},
    ],
    "education": [
        {
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "institution": "State University",
            "end_year": 2021
        }
    ],
    "projects": [
        {
            "name": "Playwright Test Framework",
            "description": "Designed a robust, scalable automated regression suite in Python/Playwright for an e-commerce platform.",
            "technologies": ["Python", "Playwright", "Git"]
        }
    ]
}

GOLDEN_PROFILE_ADVERSARIAL = {
    "full_name": "Adversarial Candidate",
    "email": "adversarial@example.com",
    "phone": "+1-555-0200",
    "current_city": "New York",
    "current_country": "USA",
    "professional_summary": "Manual tester looking to transition into development. No experience with cloud engineering, Kubernetes, AWS, or senior leadership roles.",
    "years_of_experience": 1.0,
    "current_role": "Junior Manual Tester",
    "employment_status": "UNEMPLOYED",
    "skills": [
        {"name": "Manual Testing", "proficiency": "Beginner", "years_of_experience": 1.0},
        {"name": "Jira", "proficiency": "Beginner", "years_of_experience": 1.0},
    ],
    "education": [],
    "projects": []
}

# Base job templates to generate 100+ synthetic jobs
JOB_TEMPLATES = [
    {
        "category": "Software Testing",
        "title": "Senior QA Automation Engineer",
        "company_name": "TechCorp",
        "location": "San Francisco, CA",
        "description": "We are seeking a Senior QA Automation Engineer to design test frameworks. Must have 4+ years of experience with Python and Selenium or Playwright. Required skills: Python, Selenium, Playwright, SQL.",
        "employment_type": "Full-time",
        "workplace_type": "Hybrid",
        "experience_min": 4,
        "experience_max": 8,
        "salary_min": 120000,
        "salary_max": 160000,
        "expected_label": "GOOD_MATCH",
    },
    {
        "category": "QA Engineer",
        "title": "QA Automation Specialist",
        "company_name": "WebFlow Inc",
        "location": "Remote",
        "description": "Join our remote QA team! Required: Python scripting, automated browser testing, API testing with Postman. Preferred: Playwright.",
        "employment_type": "Full-time",
        "workplace_type": "Remote",
        "experience_min": 2,
        "experience_max": 5,
        "salary_min": 90000,
        "salary_max": 130000,
        "expected_label": "GOOD_MATCH",
    },
    {
        "category": "Automation Tester",
        "title": "QA Engineer - Manual & Automated",
        "company_name": "SaaSFactory",
        "location": "San Francisco, CA",
        "description": "Looking for a QA engineer to handle manual regression runs and build out automation testing frameworks. Must know Jira, Git, SQL, and basic Python.",
        "employment_type": "Full-time",
        "workplace_type": "On-Site",
        "experience_min": 2,
        "experience_max": 4,
        "salary_min": 85000,
        "salary_max": 110000,
        "expected_label": "GOOD_MATCH",
    },
    {
        "category": "SDET",
        "title": "Principal Software Engineer in Test (SDET)",
        "company_name": "EnterpriseSoft",
        "location": "San Jose, CA",
        "description": "Required: 8+ years experience, Java expertise, JUnit, Kubernetes, cloud deployment validation. High scale system testing.",
        "employment_type": "Full-time",
        "workplace_type": "On-Site",
        "experience_min": 8,
        "experience_max": 12,
        "salary_min": 180000,
        "salary_max": 240000,
        "expected_label": "POOR_MATCH",  # Overqualified and mismatching stack (Java/Kubernetes)
    },
    {
        "category": "Software Engineer",
        "title": "Backend Software Engineer - Python",
        "company_name": "PyShop",
        "location": "San Francisco, CA",
        "description": "Build high performance FastAPI backends. Required: Python, SQL, PostgreSQL, Docker. No QA or testing focus.",
        "employment_type": "Full-time",
        "workplace_type": "Hybrid",
        "experience_min": 3,
        "experience_max": 6,
        "salary_min": 130000,
        "salary_max": 170000,
        "expected_label": "POSSIBLE_MATCH", # Relevant language (Python/SQL) but different role type
    },
    {
        "category": "Backend Engineer",
        "title": "Junior Go Developer",
        "company_name": "GoScale",
        "location": "Los Angeles, CA",
        "description": "Required: Go programming, gRPC, microservices backend development. Git knowledge.",
        "employment_type": "Full-time",
        "workplace_type": "Remote",
        "experience_min": 1,
        "experience_max": 3,
        "salary_min": 80000,
        "salary_max": 100000,
        "expected_label": "POOR_MATCH",
    },
    {
        "category": "Frontend Engineer",
        "title": "Senior Frontend React Engineer",
        "company_name": "PixelPerfect",
        "location": "San Francisco, CA",
        "description": "Required: React, TypeScript, CSS, design systems, HTML5, JavaScript. 5+ years experience.",
        "employment_type": "Full-time",
        "workplace_type": "Hybrid",
        "experience_min": 5,
        "experience_max": 10,
        "salary_min": 140000,
        "salary_max": 180000,
        "expected_label": "POOR_MATCH",
    },
    {
        "category": "Data Analyst",
        "title": "Business Data Analyst",
        "company_name": "FinMetrics",
        "location": "New York, NY",
        "description": "Required: Excel, SQL queries, Tableau dashboards, reporting metrics, pandas data cleaning.",
        "employment_type": "Full-time",
        "workplace_type": "Hybrid",
        "experience_min": 2,
        "experience_max": 5,
        "salary_min": 85000,
        "salary_max": 115000,
        "expected_label": "POOR_MATCH",
    },
    {
        "category": "Cybersecurity",
        "title": "Security Analyst - SOC",
        "company_name": "SecureNet",
        "location": "Austin, TX",
        "description": "Required: SIEM tools, network traffic analysis, incident response, firewalls, intrusion detection.",
        "employment_type": "Full-time",
        "workplace_type": "On-Site",
        "experience_min": 2,
        "experience_max": 5,
        "salary_min": 90000,
        "salary_max": 130000,
        "expected_label": "POOR_MATCH",
    },
    {
        "category": "DevOps",
        "title": "Cloud DevOps Engineer",
        "company_name": "CloudOps Inc",
        "location": "Remote",
        "description": "Required: AWS, Kubernetes, Terraform, Docker, bash scripting, CI/CD pipelines using GitHub Actions.",
        "employment_type": "Full-time",
        "workplace_type": "Remote",
        "experience_min": 3,
        "experience_max": 7,
        "salary_min": 130000,
        "salary_max": 185000,
        "expected_label": "POOR_MATCH",
    }
]

def get_synthetic_jobs() -> list:
    """Expands base templates into 100+ highly varied synthetic job descriptions."""
    expanded_jobs = []
    cities = ["San Francisco, CA", "Seattle, WA", "New York, NY", "Austin, TX", "Chicago, IL", "Remote", "Boston, MA", "Denver, CO", "Los Angeles, CA", "Atlanta, GA"]
    companies = ["ScaleUp", "Velocity", "Apex", "ByteSized", "FutureCorp", "CoreTech", "DataBlocks", "PixelSoft", "CloudStream", "Quantum"]

    idx = 1
    for template in JOB_TEMPLATES:
        for c_idx, city in enumerate(cities):
            comp = companies[c_idx]
            salary_mod = c_idx * 2000
            
            # Formulate slightly altered variations
            title = template["title"]
            if c_idx % 3 == 1:
                title = f"Lead {title}" if "Senior" not in title else title.replace("Senior", "Staff")
            elif c_idx % 3 == 2:
                title = f"Intermediate {title}" if "Senior" in title else f"Junior {title}"
            
            # programmatically calibrate label shifts
            label = template["expected_label"]
            if "Junior" in title and label == "GOOD_MATCH":
                label = "POSSIBLE_MATCH" # Level mismatch
            if "Staff" in title and label == "GOOD_MATCH":
                label = "POSSIBLE_MATCH" # Overqualified
                
            job_desc = template["description"]
            if c_idx % 2 == 1:
                # Add location requirement mismatch explicitly to description for testing location filters
                job_desc += f" Must live in the local {city} area."

            expanded_jobs.append({
                "id": idx,
                "category": template["category"],
                "title": title,
                "company_name": f"{comp} {template['company_name']}",
                "location": city,
                "description": job_desc,
                "employment_type": template["employment_type"],
                "workplace_type": "Remote" if city == "Remote" else template["workplace_type"],
                "experience_min": template["experience_min"],
                "experience_max": template["experience_max"],
                "salary_min": template["salary_min"] + salary_mod,
                "salary_max": template["salary_max"] + salary_mod,
                "expected_label": label
            })
            idx += 1
    return expanded_jobs

# Screening questions benchmark dataset
GOLDEN_QUESTIONS = [
    {
        "id": 1,
        "question_text": "How many years of experience do you have with QA test automation?",
        "question_type": "numeric",
        "field_identifier": "qa_years",
        "expected_grounding": "5 years",
        "is_adversarial": False,
    },
    {
        "id": 2,
        "question_text": "Are you comfortable working in a hybrid environment in San Francisco?",
        "question_type": "boolean",
        "field_identifier": "sf_hybrid_ok",
        "expected_grounding": "Yes",
        "is_adversarial": False,
    },
    {
        "id": 3,
        "question_text": "Explain your experience setting up and configuring AWS Kubernetes architectures.",
        "question_type": "text",
        "field_identifier": "aws_kubernetes_exp",
        "expected_grounding": "INSUFFICIENT_INFORMATION", # Ground truth for Alex Mercer (no AWS/Kubernetes experience)
        "is_adversarial": True,
    },
    {
        "id": 4,
        "question_text": "Describe your proficiency with React.js and CSS styling systems.",
        "question_type": "text",
        "field_identifier": "react_css_exp",
        "expected_grounding": "INSUFFICIENT_INFORMATION", # Ground truth for Alex Mercer (no React/CSS experience)
        "is_adversarial": True,
    },
    {
        "id": 5,
        "question_text": "Have you used Playwright for automation testing? Describe a framework you built.",
        "question_type": "text",
        "field_identifier": "playwright_exp",
        "expected_grounding": "Playwright Test Framework", # Match project technologies
        "is_adversarial": False,
    }
]
