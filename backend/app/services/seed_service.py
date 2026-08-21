from sqlalchemy.orm import Session
from app.models.profile import (
    User,
    UserProfile,
    Education,
    Skill,
    Project,
    Certification,
    JobPreference,
    ApplicationPreference,
)


def seed_sample_profile(db: Session, user_id: int = 1) -> UserProfile:
    """
    Seeds development-only sample user profile with realistic fake data for testing.
    """
    # 1. Ensure User exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email="test.user@example.com")
        db.add(user)
        db.commit()

    # 2. Check existing profile and clear children if recreating
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        db.delete(profile)
        db.commit()

    # 3. Create sample UserProfile
    profile = UserProfile(
        user_id=user_id,
        full_name="Test User",
        email="test.user@example.com",
        phone="+1-555-0199",
        current_city="San Francisco",
        current_country="USA",
        professional_summary="Passionate Full Stack & Automation Engineer with expertise in Python, FastAPI, React, and browser automation tools.",
        years_of_experience=3.5,
        current_role="Software Engineer",
        employment_status="Employed",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 4. Add Education records
    edu1 = Education(
        profile_id=profile.id,
        institution="State Tech University",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
        start_year=2018,
        end_year=2022,
        grade_or_cgpa="3.8/4.0",
    )
    db.add(edu1)

    # 5. Add Skills
    skills_data = [
        ("Python", "Programming", "Expert", 3.5),
        ("FastAPI", "Framework", "Intermediate", 2.0),
        ("PostgreSQL", "Database", "Intermediate", 2.5),
        ("Playwright", "Testing", "Intermediate", 1.5),
        ("React", "Framework", "Intermediate", 2.0),
        ("Git & DevOps", "DevOps", "Intermediate", 3.0),
    ]
    for name, cat, prof, yoe in skills_data:
        db.add(Skill(profile_id=profile.id, name=name, category=cat, proficiency=prof, years_of_experience=yoe))

    # 6. Add Project
    proj1 = Project(
        profile_id=profile.id,
        name="JobPilot Platform",
        description="AI-assisted job application automation platform built with Python, FastAPI, and Playwright.",
        technologies=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "React", "Playwright"],
        project_url="https://github.com/example/jobpilot",
        start_date="2026-01",
        end_date="2026-08",
    )
    db.add(proj1)

    # 7. Add Certification
    cert1 = Certification(
        profile_id=profile.id,
        name="AWS Certified Solutions Architect",
        issuing_organization="Amazon Web Services",
        issue_date="2024-05",
        expiry_date="2027-05",
        credential_url="https://aws.amazon.com/verification/example123",
    )
    db.add(cert1)

    # 8. Add Job Preferences
    job_pref = JobPreference(
        profile_id=profile.id,
        target_roles=["Software Engineer", "Backend Developer", "QA Automation Engineer"],
        preferred_locations=["San Francisco", "New York", "Remote"],
        work_arrangements=["hybrid", "remote"],
        employment_types=["full-time"],
        min_expected_salary=100000.0,
        max_expected_salary=140000.0,
        salary_currency="USD",
        min_required_experience=2.0,
        max_acceptable_experience=5.0,
        relocation_status="willing",
        authorized_to_work=True,
        requires_sponsorship=False,
    )
    db.add(job_pref)

    # 9. Add Application Preferences
    app_pref = ApplicationPreference(
        profile_id=profile.id,
        min_job_match_score=75.0,
        max_applications_per_day=15,
        require_approval_before_submission=True,  # Safety default
        allow_generated_answers=True,
        allow_resume_tailoring=True,
        preferred_application_sources=["LinkedIn", "CompanyCareer"],
    )
    db.add(app_pref)

    db.commit()
    db.refresh(profile)
    return profile
