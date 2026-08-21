import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/mock", tags=["Local Mock Job Application Server"])

MOCK_PAGES_DIR = os.path.abspath("./storage/mock_pages")

MOCK_SUBMITTED_APPLICATIONS: List[Dict[str, Any]] = []

SYNTHETIC_MOCK_JOB = {
    "id": 101,
    "company": "Acme Technologies",
    "title": "Junior QA Engineer",
    "location": "Bangalore, India",
    "employment_type": "FULL_TIME",
    "workplace_type": "HYBRID",
    "description": "A synthetic QA role requiring testing fundamentals, SQL, Selenium, and API testing.",
}


def ensure_mock_html_files():
    """Generates static mock HTML files for instant file:// Playwright navigation."""
    os.makedirs(MOCK_PAGES_DIR, exist_ok=True)

    step1_path = os.path.join(MOCK_PAGES_DIR, "step1.html")
    step2_path = os.path.join(MOCK_PAGES_DIR, "step2.html")
    step3_path = os.path.join(MOCK_PAGES_DIR, "step3.html")
    review_path = os.path.join(MOCK_PAGES_DIR, "review.html")
    captcha_path = os.path.join(MOCK_PAGES_DIR, "captcha.html")

    step1_html = f"""<!DOCTYPE html>
<html>
<head><title>Acme Technologies Application - Step 1</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h2>Acme Technologies — Job Application (Step 1 of 3)</h2>
    <p><strong>Role:</strong> Junior QA Engineer</p>
    
    <form id="step1-form" action="file://{step2_path}" method="GET">
        <div style="margin-bottom: 1rem;">
            <label for="fullNameInput">Full Name *</label><br/>
            <input type="text" id="fullNameInput" name="applicant_name" required style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="emailInput">Email Address *</label><br/>
            <input type="email" id="emailInput" name="candidate_email" required style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="phoneInput">Mobile Number *</label><br/>
            <input type="tel" id="phoneInput" name="candidate_phone" required style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="cityInput">Current City *</label><br/>
            <input type="text" id="cityInput" name="current_city" required style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="countrySelect">Country *</label><br/>
            <select id="countrySelect" name="country_name" required style="width: 310px; padding: 0.5rem;">
                <option value="">-- Select Country --</option>
                <option value="India">India</option>
                <option value="United States">United States</option>
            </select>
        </div>
        <button type="submit" id="next-btn-step1" style="padding: 0.6rem 1.2rem; background: #1976d2; color: white; border: none; cursor: pointer;">Next: Education & Experience &rarr;</button>
    </form>
</body>
</html>"""

    step2_html = f"""<!DOCTYPE html>
<html>
<head><title>Acme Technologies Application - Step 2</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h2>Acme Technologies — Job Application (Step 2 of 3)</h2>
    
    <form id="step2-form" action="file://{step3_path}" method="GET">
        <div style="margin-bottom: 1rem;">
            <label for="degreeInput">Highest Degree Qualification *</label><br/>
            <input type="text" id="degreeInput" name="degree_title" required placeholder="e.g. B.Tech Computer Science" style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="institutionInput">College / University *</label><br/>
            <input type="text" id="institutionInput" name="college_name" required style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="gradYearInput">Graduation Year *</label><br/>
            <input type="number" id="gradYearInput" name="graduation_year" required style="width: 150px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="expInput">Years of Experience *</label><br/>
            <input type="number" step="0.5" id="expInput" name="years_exp" required style="width: 150px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="roleInput">Current / Most Recent Role</label><br/>
            <input type="text" id="roleInput" name="current_role_title" style="width: 300px; padding: 0.5rem;" />
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="skillsInput">Primary Technical Skills</label><br/>
            <input type="text" id="skillsInput" name="skills_list" placeholder="e.g. Selenium, SQL, Python" style="width: 300px; padding: 0.5rem;" />
        </div>
        <button type="submit" id="next-btn-step2" style="padding: 0.6rem 1.2rem; background: #1976d2; color: white; border: none; cursor: pointer;">Next: Preferences & Resume &rarr;</button>
    </form>
</body>
</html>"""

    step3_html = f"""<!DOCTYPE html>
<html>
<head><title>Acme Technologies Application - Step 3</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h2>Acme Technologies — Job Application (Step 3 of 3)</h2>
    
    <form id="step3-form" action="file://{review_path}" method="GET">
        <div style="margin-bottom: 1rem;">
            <label>Willing to Relocate? *</label><br/>
            <input type="radio" id="relocate-yes" name="relocate_opt" value="Yes" /> <label for="relocate-yes">Yes</label>
            <input type="radio" id="relocate-no" name="relocate_opt" value="No" /> <label for="relocate-no">No</label>
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="workplaceSelect">Preferred Workplace Arrangement *</label><br/>
            <select id="workplaceSelect" name="workplace_pref" required style="width: 300px; padding: 0.5rem;">
                <option value="HYBRID">Hybrid</option>
                <option value="REMOTE">Remote</option>
            </select>
        </div>
        <div style="margin-bottom: 1.5rem;">
            <label for="resumeUpload">Upload Resume Document (PDF/DOCX) *</label><br/>
            <input type="file" id="resumeUpload" name="resume_file" accept=".pdf,.docx" required style="padding: 0.5rem 0;" />
        </div>
        <hr/>
        <h3>Screening Questions</h3>
        <div style="margin-bottom: 1rem;">
            <label for="q1Input">Why are you interested in this role? *</label><br/>
            <textarea id="q1Input" name="q_interest" rows="3" style="width: 400px; padding: 0.5rem;"></textarea>
        </div>
        <div style="margin-bottom: 1rem;">
            <label for="q2Input">Describe your relevant experience in software testing. *</label><br/>
            <textarea id="q2Input" name="q_experience" rows="3" style="width: 400px; padding: 0.5rem;"></textarea>
        </div>
        <button type="submit" id="review-btn" style="padding: 0.6rem 1.2rem; background: #2e7d32; color: white; border: none; cursor: pointer;">Proceed to Review Application &rarr;</button>
    </form>
</body>
</html>"""

    review_html = """<!DOCTYPE html>
<html>
<head><title>Acme Technologies Application - Review</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h2>Acme Technologies — Review Application</h2>
    <div style="background: #e8f5e9; border: 1px solid #a5d6a7; padding: 1rem; border-radius: 6px;">
        <h3>Application Ready for Final Review</h3>
        <p><strong>Status:</strong> READY_FOR_REVIEW (Agent stopped safely before submission)</p>
    </div>
    <div style="margin-top: 1.5rem;">
        <button id="final-submit-btn" disabled style="padding: 0.8rem 1.5rem; background: #888; color: white; border: none; cursor: not-allowed;">Submit Application (Disabled by Safety Policy)</button>
    </div>
</body>
</html>"""

    captcha_html = """<!DOCTYPE html>
<html>
<head><title>Security Check - CAPTCHA Required</title></head>
<body style="font-family: sans-serif; padding: 2rem; text-align: center;">
    <h2 style="color: #c62828;">Security Verification (CAPTCHA)</h2>
    <div id="g-recaptcha" class="g-recaptcha" style="border: 2px dashed #999; padding: 2rem; display: inline-block;">
        [Mock Google reCAPTCHA Challenge Widget]
    </div>
</body>
</html>"""

    with open(step1_path, "w", encoding="utf-8") as f: f.write(step1_html)
    with open(step2_path, "w", encoding="utf-8") as f: f.write(step2_html)
    with open(step3_path, "w", encoding="utf-8") as f: f.write(step3_html)
    with open(review_path, "w", encoding="utf-8") as f: f.write(review_html)
    with open(captcha_path, "w", encoding="utf-8") as f: f.write(captcha_html)

    return f"file://{step1_path}"


# Ensure files exist at startup
ensure_mock_html_files()


@router.get("/jobs", response_model=List[Dict[str, Any]])
def list_mock_jobs():
    return [SYNTHETIC_MOCK_JOB]


@router.get("/jobs/{id}")
def get_mock_job(id: int):
    if id != 101:
        raise HTTPException(status_code=404, detail="Mock job not found.")
    return SYNTHETIC_MOCK_JOB


@router.get("/apply/{id}/step/1", response_class=HTMLResponse)
def get_mock_apply_step1(id: int):
    step1_path = os.path.join(MOCK_PAGES_DIR, "step1.html")
    with open(step1_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/apply/{id}/step/2", response_class=HTMLResponse)
def get_mock_apply_step2(id: int):
    step2_path = os.path.join(MOCK_PAGES_DIR, "step2.html")
    with open(step2_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/apply/{id}/step/3", response_class=HTMLResponse)
def get_mock_apply_step3(id: int):
    step3_path = os.path.join(MOCK_PAGES_DIR, "step3.html")
    with open(step3_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/apply/{id}/review", response_class=HTMLResponse)
def get_mock_apply_review(id: int):
    review_path = os.path.join(MOCK_PAGES_DIR, "review.html")
    with open(review_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/apply/{id}/captcha", response_class=HTMLResponse)
def get_mock_captcha_page(id: int):
    captcha_path = os.path.join(MOCK_PAGES_DIR, "captcha.html")
    with open(captcha_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.post("/api/submit")
def submit_mock_application(data: Dict[str, Any]):
    MOCK_SUBMITTED_APPLICATIONS.append(data)
    return JSONResponse(status_code=201, content={"status": "submitted", "id": len(MOCK_SUBMITTED_APPLICATIONS)})


# --- SYNTHETIC CAREER SITES ---

@router.get("/synthetic-careers/site_a", response_class=HTMLResponse)
def get_site_a(page: int = 1):
    jobs_list = [
        {"id": 1, "title": "Frontend Engineer", "company": "TechCorp A", "location": "Remote, US"},
        {"id": 2, "title": "Data Scientist", "company": "TechCorp A", "location": "New York, NY"},
    ]
    if page > 1:
        jobs_list = [
            {"id": 3, "title": "DevOps Engineer", "company": "TechCorp A", "location": "Austin, TX"},
        ]
    
    cards_html = ""
    for j in jobs_list:
        cards_html += f"""
        <div class="job-card" style="border: 1px solid #ccc; padding: 1rem; margin-bottom: 1rem;">
            <h3 class="job-title">{j["title"]}</h3>
            <span class="job-company">{j["company"]}</span>
            <span class="job-location">{j["location"]}</span>
            <a class="job-link" href="http://localhost:8000/mock/synthetic-careers/site_a/job/{j['id']}">View Details</a>
        </div>
        """
        
    next_link = f'<a class="next-page" href="http://localhost:8000/mock/synthetic-careers/site_a?page={page+1}">Next Page</a>' if page == 1 else ''
    
    html_content = f"""
    <html>
        <head><title>TechCorp A Careers - Page {page}</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>TechCorp A Careers Portal</h2>
            <div id="job-listings">{cards_html}</div>
            <div class="pagination">{next_link}</div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/synthetic-careers/site_a/job/{id}", response_class=HTMLResponse)
def get_site_a_job(id: int):
    jobs_db = {
        1: {"title": "Frontend Engineer", "company": "TechCorp A", "location": "Remote, US", "description": "React development job. Requires 3+ years experience.", "salary": "120000", "exp": "3"},
        2: {"title": "Data Scientist", "company": "TechCorp A", "location": "New York, NY", "description": "Machine learning modeling. Requires Python, SQL, PyTorch.", "salary": "150000", "exp": "4"},
        3: {"title": "DevOps Engineer", "company": "TechCorp A", "location": "Austin, TX", "description": "AWS infrastructure scaling. Kubernetes and CI/CD pipelines.", "salary": "140000", "exp": "5"},
    }
    job = jobs_db.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    html_content = f"""
    <html>
        <head><title>{job['title']} - TechCorp A</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>{job['title']}</h2>
            <div class="job-company">{job['company']}</div>
            <div class="job-location">{job['location']}</div>
            <div class="job-description">{job['description']}</div>
            <div class="job-salary">{job['salary']}</div>
            <div class="job-experience">{job['exp']}</div>
            <a class="apply-url" href="http://localhost:8000/mock/synthetic-careers/site_a/job/{id}/apply">Apply Now</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/synthetic-careers/site_b", response_class=HTMLResponse)
def get_site_b():
    json_ld_data = [
        {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": "Backend Developer",
            "description": "We are seeking a Python / Django Developer. Postings must be standard.",
            "datePosted": "2026-08-20T00:00:00Z",
            "hiringOrganization": {
                "@type": "Organization",
                "name": "Innovate Ltd",
                "sameAs": "https://innovateltd.com"
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "London",
                    "addressCountry": "UK"
                }
            },
            "employmentType": "FULL_TIME",
            "identifier": {
                "@type": "PropertyValue",
                "name": "Innovate Ltd",
                "value": "INV-201"
            },
            "baseSalary": {
                "@type": "MonetaryAmount",
                "currency": "GBP",
                "value": {
                    "@type": "QuantitativeValue",
                    "value": 85000,
                    "unitText": "YEAR"
                }
            }
        },
        {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": "Data Engineer",
            "description": "SQL and Spark pipeline building. Large data processing experience required.",
            "datePosted": "2026-08-21T00:00:00Z",
            "hiringOrganization": {
                "@type": "Organization",
                "name": "Innovate Ltd",
                "sameAs": "https://innovateltd.com"
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "London",
                    "addressCountry": "UK"
                }
            },
            "employmentType": "CONTRACT",
            "identifier": {
                "@type": "PropertyValue",
                "name": "Innovate Ltd",
                "value": "INV-202"
            },
            "baseSalary": {
                "@type": "MonetaryAmount",
                "currency": "GBP",
                "value": {
                    "@type": "QuantitativeValue",
                    "value": 95000,
                    "unitText": "YEAR"
                }
            }
        }
    ]
    import json
    json_ld_str = json.dumps(json_ld_data)
    
    html_content = f"""
    <html>
        <head>
            <title>Innovate Ltd Careers</title>
            <script type="application/ld+json">
            {json_ld_str}
            </script>
        </head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>Innovate Ltd Careers Portal (JSON-LD)</h2>
            <p>All job openings are stored in structured JSON-LD format in the head metadata.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/synthetic-careers/site_c", response_class=HTMLResponse)
def get_site_c(page: int = 1):
    jobs_list = [
        {"id": 4, "title": "Cloud Architect", "company": "CloudSys", "location": "San Francisco, CA"},
    ]
    if page > 1:
        jobs_list = [
            {"id": 5, "title": "Security Analyst", "company": "CloudSys", "location": "Seattle, WA"},
        ]
        
    items_html = ""
    for j in jobs_list:
        items_html += f"""
        <article class="job-item" style="border: 1px dashed blue; padding: 1.2rem; margin-bottom: 0.8rem;">
            <h2 class="title-class"><a class="link-class" href="http://localhost:8000/mock/synthetic-careers/site_c/job/{j['id']}">{j["title"]}</a></h2>
            <div class="company-class">{j["company"]}</div>
            <div class="loc-class">{j["location"]}</div>
        </article>
        """
        
    pagination_button = f'<button class="load-more-btn" onclick="location.href=\'http://localhost:8000/mock/synthetic-careers/site_c?page={page+1}\'">Load More</button>' if page == 1 else ''
    
    html_content = f"""
    <html>
        <head><title>CloudSys Job Postings - Page {page}</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>CloudSys Careers Site</h2>
            <section class="listings">{items_html}</section>
            <div class="navigation">{pagination_button}</div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/synthetic-careers/site_c/job/{id}", response_class=HTMLResponse)
def get_site_c_job(id: int):
    jobs_db = {
        4: {"title": "Cloud Architect", "company": "CloudSys", "location": "San Francisco, CA", "description": "AWS architecture & cost optimization role. Requires 8+ years experience.", "salary": "180000"},
        5: {"title": "Security Analyst", "company": "CloudSys", "location": "Seattle, WA", "description": "SOC analyst role, network traffic monitoring, threat hunting.", "salary": "110000"},
    }
    job = jobs_db.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    html_content = f"""
    <html>
        <head><title>{job['title']} - CloudSys</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>{job['title']}</h2>
            <div class="company-class">{job['company']}</div>
            <div class="loc-class">{job['location']}</div>
            <div class="desc-class">{job['description']}</div>
            <div class="salary-class">{job['salary']}</div>
            <a class="app-url-class" href="http://localhost:8000/mock/apply-now/{id}">Apply Now</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
