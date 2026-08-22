from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import (
    User,
    UserProfile,
    Education,
    Skill,
    Project,
    Certification,
    JobPreference,
    ApplicationPreference,
    Resume,
    Job,
    JobSource,
    JobMatch,
    ApplicationPackage,
    TailoredResume,
    ApplicationQuestion,
    ApplicationAnswer,
    Application,
    ApplicationQueue,
    SubmissionAuthorization,
    SubmissionRun,
    OrchestrationRun,
    PackageVersion,
)
from app.services.automation.execution_worker import ApplicationExecutionWorker

DEMO_USER_ID = 99999

def clear_demo_data(db: Session):
    """
    Clears all database records associated with the demo user (ID 99999).
    """
    # 1. Find profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == DEMO_USER_ID).first()
    if profile:
        profile_id = profile.id
        
        # Delete related applications and submission objects
        apps = db.query(Application).filter(Application.profile_id == profile_id).all()
        for app in apps:
            db.query(ApplicationQueue).filter(ApplicationQueue.application_id == app.id).delete()
            db.query(SubmissionAuthorization).filter(SubmissionAuthorization.application_id == app.id).delete()
            db.query(SubmissionRun).filter(SubmissionRun.application_id == app.id).delete()
            db.query(ApplicationPackage).filter(ApplicationPackage.job_id == app.job_id, ApplicationPackage.profile_id == profile_id).delete()
            db.delete(app)
            
        # Delete other details
        db.query(Education).filter(Education.profile_id == profile_id).delete()
        db.query(Skill).filter(Skill.profile_id == profile_id).delete()
        db.query(Project).filter(Project.profile_id == profile_id).delete()
        db.query(Certification).filter(Certification.profile_id == profile_id).delete()
        db.query(JobPreference).filter(JobPreference.profile_id == profile_id).delete()
        db.query(ApplicationPreference).filter(ApplicationPreference.profile_id == profile_id).delete()
        db.query(Resume).filter(Resume.profile_id == profile_id).delete()
        db.query(JobMatch).filter(JobMatch.profile_id == profile_id).delete()
        db.query(OrchestrationRun).filter(OrchestrationRun.profile_id == profile_id).delete()
        
        db.delete(profile)
        
    db.query(User).filter(User.id == DEMO_USER_ID).delete()
    db.commit()

def seed_demo_data(db: Session) -> UserProfile:
    """
    Seeds complete synthetic demo scenario data for User ID 99999.
    Deterministic and duplicate-safe.
    """
    # Clear existing demo data first to ensure clean state
    clear_demo_data(db)

    # 1. Create Demo User
    user = User(id=DEMO_USER_ID, email="demo.pilot@jobpilot.io")
    db.add(user)
    db.commit()

    # 2. Create Demo User Profile
    profile = UserProfile(
        user_id=DEMO_USER_ID,
        full_name="Alex Mercer",
        email="alex.mercer@demo.com",
        phone="+1-555-0720",
        current_city="Seattle",
        current_country="USA",
        professional_summary="Senior QA Automation & Test Infrastructure Engineer with 6+ years of experience designing scalable UI/API test frameworks using Python, Playwright, Selenium, and CI/CD pipelines.",
        years_of_experience=6.2,
        current_role="QA Automation Engineer",
        employment_status="Open to Opportunities",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 3. Add Education
    edu = Education(
        profile_id=profile.id,
        institution="University of Washington",
        degree="B.S. in Computer Science",
        field_of_study="Software Engineering",
        start_year=2016,
        end_year=2020,
        grade_or_cgpa="3.7/4.0",
    )
    db.add(edu)

    # 4. Add Skills
    skills = [
        ("Python", "Programming", "Expert", 6.0),
        ("JavaScript", "Programming", "Intermediate", 3.0),
        ("Playwright", "Testing", "Expert", 3.0),
        ("Selenium", "Testing", "Expert", 5.0),
        ("PostgreSQL", "Database", "Intermediate", 4.0),
        ("Docker", "DevOps", "Intermediate", 3.0),
        ("GitHub Actions", "DevOps", "Intermediate", 4.0),
    ]
    for name, cat, prof, yoe in skills:
        db.add(Skill(profile_id=profile.id, name=name, category=cat, proficiency=prof, years_of_experience=yoe))

    # 5. Add Projects
    proj = Project(
        profile_id=profile.id,
        name="AutoTest-Core Framework",
        description="Created a modular testing library that reduced API regression suite times by 40% using concurrent routing.",
        technologies=["Python", "FastAPI", "Docker", "Pytest"],
        project_url="https://github.com/alexmercer/autotest-core",
        start_date="2024-03",
        end_date="2025-01",
    )
    db.add(proj)

    # 6. Add Certifications
    cert = Certification(
        profile_id=profile.id,
        name="Certified Software Test Engineer (CSTE)",
        issuing_organization="Software Certifications Board",
        issue_date="2022-09",
        expiry_date="2027-09",
    )
    db.add(cert)

    # 7. Add Preferences
    job_pref = JobPreference(
        profile_id=profile.id,
        target_roles=["QA Automation Engineer", "Software Development Engineer in Test", "QA Manager"],
        preferred_locations=["Seattle", "San Francisco", "Remote"],
        work_arrangements=["hybrid", "remote"],
        employment_types=["full-time"],
        min_expected_salary=115000.0,
        max_expected_salary=150000.0,
        salary_currency="USD",
        min_required_experience=4.0,
        max_acceptable_experience=8.0,
        relocation_status="willing",
        authorized_to_work=True,
        requires_sponsorship=False,
    )
    db.add(job_pref)

    app_pref = ApplicationPreference(
        profile_id=profile.id,
        min_job_match_score=70.0,
        max_applications_per_day=10,
        require_approval_before_submission=True,
        allow_generated_answers=True,
        allow_resume_tailoring=True,
        preferred_application_sources=["LinkedIn", "Greenhouse", "Lever", "CompanyCareer"],
    )
    db.add(app_pref)

    # 8. Add Demo Master Resume
    resume = Resume(
        profile_id=profile.id,
        name="Alex Mercer Master QA Resume.pdf",
        original_filename="alex_mercer_master_qa_resume.pdf",
        file_path="storage/resumes/alex_mercer_master_qa_resume.pdf",
        file_type="PDF",
        file_size=1048576,
        is_default=True,
        processing_status="PROCESSED",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 9. Seed Job Sources if missing
    sources = ["linkedin", "greenhouse", "lever", "company_career"]
    for src in sources:
        s_obj = db.query(JobSource).filter(JobSource.name == src).first()
        if not s_obj:
            s_obj = JobSource(name=src, display_name=src.replace("_", " ").capitalize(), enabled=True, source_type="API")
            db.add(s_obj)
    db.commit()

    # Enable mock configs
    for name in ["mock_platform", "company_career", "greenhouse", "lever", "linkedin"]:
        cfg = ApplicationExecutionWorker.get_or_create_source_config(db, name)
        cfg.enabled = True
    db.commit()

    # 10. Add Jobs
    # Job 1: High Match (92%)
    job1 = Job(
        title="Senior QA Automation Engineer",
        company_name="TechGiant Inc",
        location="Seattle, WA · Hybrid",
        application_url="http://localhost:8000/mock/apply/901",
        description="We are seeking a Senior QA Engineer to build test automation frameworks with Python and Playwright. Experience with Selenium and CI/CD pipelines is required.",
        status="ACTIVE",
    )
    db.add(job1)

    # Job 2: Strong Match (88%)
    job2 = Job(
        title="SDET - Test Infrastructure",
        company_name="FintechCorp",
        location="Remote · USA",
        application_url="http://localhost:8000/mock/apply/902",
        description="Looking for an SDET to build test platforms. Strong Python or JavaScript programming skills, Docker experience, and automation test building.",
        status="ACTIVE",
    )
    db.add(job2)

    # Job 3: Decent Match (78%)
    job3 = Job(
        title="Software Engineer in Test",
        company_name="CloudSolutions",
        location="Seattle, WA · On-Site",
        application_url="http://localhost:8000/mock/apply/903",
        description="Focus on automation and release quality. Automation scripting experience, SQL knowledge, and test strategy development.",
        status="ACTIVE",
    )
    db.add(job3)

    # Job 4: Low Match (55%)
    job4 = Job(
        title="Java Software Developer",
        company_name="OldTech Industries",
        location="Bellevue, WA · On-Site",
        application_url="http://localhost:8000/mock/apply/904",
        description="Maintain legacy Java backend application. Oracle DB query writing, Spring Framework experience, manual sanity testing code.",
        status="ACTIVE",
    )
    db.add(job4)

    # Job 5: Skip-worthy (45%)
    job5 = Job(
        title="Manual QA Tester",
        company_name="BizApps Co",
        location="Seattle, WA",
        application_url="http://localhost:8000/mock/apply/905",
        description="Perform manual exploratory testing, document detailed test steps, verify UI bugs, work alongside development teams.",
        status="ACTIVE",
    )
    db.add(job5)
    db.commit()
    db.refresh(job1)
    db.refresh(job2)
    db.refresh(job3)
    db.refresh(job4)
    db.refresh(job5)

    # 11. Add Match Scores
    db.add(JobMatch(profile_id=profile.id, job_id=job1.id, overall_score=92.0, recommendation="APPLY", eligible=True, strengths=["Python", "Playwright", "Selenium", "CI/CD"], concerns=["Kubernetes"]))
    db.add(JobMatch(profile_id=profile.id, job_id=job2.id, overall_score=88.0, recommendation="APPLY", eligible=True, strengths=["Python", "JavaScript", "Docker"], concerns=["No manual QA mentioned"]))
    db.add(JobMatch(profile_id=profile.id, job_id=job3.id, overall_score=78.0, recommendation="REVIEW", eligible=True, strengths=["SQL", "Test strategy"], concerns=["On-Site requirement"]))
    db.add(JobMatch(profile_id=profile.id, job_id=job4.id, overall_score=55.0, recommendation="SKIP", eligible=False, strengths=["Oracle DB"], concerns=["Java required", "Legacy stack"]))
    db.add(JobMatch(profile_id=profile.id, job_id=job5.id, overall_score=45.0, recommendation="SKIP", eligible=False, strengths=["Manual testing"], concerns=["No automation involved"]))
    db.commit()

    # 12. Create tailored resume
    tailored_res1 = TailoredResume(
        profile_id=profile.id,
        source_resume_id=resume.id,
        job_id=job1.id,
        title="Alex Mercer Tailored Resume - TechGiant.pdf",
        status="VALIDATED",
        pdf_file_path="storage/resumes/alex_mercer_tailored_techgiant.pdf",
        relevance_score=92.0,
        structured_content={"summary": "Tailored QA Automation summary for TechGiant Inc..."},
        change_report={"added_keywords": ["Playwright", "CI/CD"]},
        keyword_analysis={"coverage": 95.0}
    )
    db.add(tailored_res1)
    db.commit()
    db.refresh(tailored_res1)

    # 13. Create application packages & versions
    pkg1 = ApplicationPackage(
        profile_id=profile.id,
        job_id=job1.id,
        source_resume_id=resume.id,
        tailored_resume_id=tailored_res1.id,
        status="READY_FOR_REVIEW",
        package_summary={
            "matching_skills": ["Python", "Playwright", "Selenium", "CI/CD"],
            "missing_skills": ["Kubernetes"],
            "strengths": ["6+ years test framework design", "Strong Python background"],
            "concerns": ["No Java background (job requires minimal Java knowledge)"]
        },
        validation_result={"valid": True, "warnings": []}
    )
    db.add(pkg1)
    db.commit()
    db.refresh(pkg1)

    ver1 = PackageVersion(
        application_package_id=pkg1.id,
        version=1,
        package_content={
            "resume": "Tailored Resume Content for TechGiant Inc...",
            "answers": [
                {
                    "question": "How many years of experience do you have with Selenium?",
                    "answer": "I have over 5 years of experience using Selenium for UI automation suite building.",
                    "confidence": 0.95,
                    "id": 1
                },
                {
                    "question": "Why are you interested in this role?",
                    "answer": "TechGiant Inc builds cutting-edge infrastructure, and I am excited to apply my Playwright and Python framework design skills here.",
                    "confidence": 0.90,
                    "id": 2
                }
            ]
        },
        approved=False
    )
    db.add(ver1)

    # 14. Create screening questions & answers
    q1 = ApplicationQuestion(
        job_id=job1.id,
        question_text="How many years of experience do you have with Selenium?",
        field_identifier="selenium_years",
        question_type="numeric",
        required=True,
        classification_confidence=0.95,
        answer_source="PROFILE"
    )
    db.add(q1)
    db.commit()
    db.refresh(q1)

    a1 = ApplicationAnswer(
        question_id=q1.id,
        answer_text="5 years",
        answer_status="VALIDATED",
        confidence=0.95,
        generated_by="AI_MODEL",
        validation_result={"valid": True}
    )
    db.add(a1)

    q2 = ApplicationQuestion(
        job_id=job1.id,
        question_text="Why are you interested in this role?",
        field_identifier="role_interest",
        question_type="text",
        required=True,
        classification_confidence=0.90,
        answer_source="AI_GENERATED"
    )
    db.add(q2)
    db.commit()
    db.refresh(q2)

    a2 = ApplicationAnswer(
        question_id=q2.id,
        answer_text="TechGiant Inc builds cutting-edge infrastructure, and I am excited to apply my Playwright and Python framework design skills here.",
        answer_status="NEEDS_REVIEW",
        confidence=0.90,
        generated_by="AI_MODEL",
        validation_result={"valid": True}
    )
    db.add(a2)
    db.commit()

    # 15. Create Applications
    # App 1: Needs review
    app1 = Application(
        profile_id=profile.id,
        job_id=job1.id,
        application_package_id=pkg1.id,
        selected_resume_id=resume.id,
        tailored_resume_id=tailored_res1.id,
        status="REVIEW",
        source="company_career",
        application_url=job1.application_url
    )
    db.add(app1)

    # App 2: Already submitted successfully
    app2 = Application(
        profile_id=profile.id,
        job_id=job2.id,
        status="SUBMITTED",
        source="greenhouse",
        application_url=job2.application_url,
        submitted_at=datetime.now() - timedelta(hours=4)
    )
    db.add(app2)

    # 14. Seed structured demo run history
    run = OrchestrationRun(
        profile_id=profile.id,
        status="COMPLETED",
        trigger_type="MANUAL",
        started_at=datetime.now() - timedelta(hours=5),
        completed_at=datetime.now() - timedelta(hours=4, minutes=50),
        jobs_discovered=5,
        jobs_matched=3,
        jobs_selected=3,
        packages_created=1,
        applications_ready=1,
        applications_submitted=1,
        error_count=0
    )
    db.add(run)
    db.commit()

    return profile
