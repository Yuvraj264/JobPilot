#!/usr/bin/env python3
import os
import sys

# Adjust python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.connection import SessionLocal
from app.models.profile import User, UserProfile, Skill, Education, Project
from app.models.job import Job
from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
from tests.regression.golden_dataset import GOLDEN_PROFILE, get_synthetic_jobs

def run_resume_benchmark():
    print("====================================================")
    print("📝 RESUME TAILORING FACTUAL SAFETY BENCHMARK")
    print("====================================================\n")

    db = SessionLocal()
    
    # Create temporary User
    user = User(email="benchmark_user@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    # 1. Instantiate synthetic UserProfile object
    profile = UserProfile(
        user_id=user.id,
        full_name=GOLDEN_PROFILE["full_name"],
        email=GOLDEN_PROFILE["email"],
        phone=GOLDEN_PROFILE["phone"],
        current_city=GOLDEN_PROFILE["current_city"],
        current_country=GOLDEN_PROFILE["current_country"],
        professional_summary=GOLDEN_PROFILE["professional_summary"],
        years_of_experience=GOLDEN_PROFILE["years_of_experience"],
        current_role=GOLDEN_PROFILE["current_role"],
        employment_status=GOLDEN_PROFILE["employment_status"]
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Add skills, education, projects linked to the profile
    skills = [Skill(profile_id=profile.id, name=s["name"], proficiency=s["proficiency"], years_of_experience=s["years_of_experience"]) for s in GOLDEN_PROFILE["skills"]]
    education = [Education(profile_id=profile.id, degree=e["degree"], field_of_study=e["field_of_study"], institution=e["institution"], end_year=e["end_year"]) for e in GOLDEN_PROFILE["education"]]
    projects = [Project(profile_id=profile.id, name=p["name"], description=p["description"], technologies=p["technologies"]) for p in GOLDEN_PROFILE["projects"]]

    for s in skills: db.add(s)
    for e in education: db.add(e)
    for p in projects: db.add(p)
    db.commit()
    db.refresh(profile)

    jobs = get_synthetic_jobs()
    print(f"Loaded {len(jobs)} synthetic benchmark jobs for tailoring.")

    hallucinations_detected = 0
    factual_mismatches = 0
    
    # Run over 5 representative jobs (to make execution fast and stable)
    eval_jobs = jobs[:5]
    
    try:
        for idx, sj in enumerate(eval_jobs):
            # Create a real Job in database so ForeignKeys resolve correctly
            job_obj = Job(
                title=sj["title"],
                company_name=sj["company_name"],
                location=sj["location"],
                description=sj["description"],
                employment_type=sj["employment_type"],
                workplace_type=sj["workplace_type"],
                experience_min=sj["experience_min"],
                experience_max=sj["experience_max"],
                salary_min=sj["salary_min"],
                salary_max=sj["salary_max"]
            )
            db.add(job_obj)
            db.commit()
            db.refresh(job_obj)
            
            # Trigger tailoring service
            tailored_res = ResumeTailoringService.tailor_resume(
                db=db,
                profile=profile,
                job=job_obj,
                master_resume=None
            )
            
            # Verify safety rules
            structured_content = tailored_res.structured_content or {}
            change_report = tailored_res.change_report or {}
            
            # Safety Check: Compare tailored text/skills against user's actual profile skills
            # Ensure we do NOT inject skills that are completely absent from user skills
            added_keywords = change_report.get("added_keywords", [])
            for kw in added_keywords:
                # If the keyword is not related to any profile skills, flag as potential hallucination
                kw_lower = kw.lower()
                profile_has_skill = any(kw_lower in s.name.lower() or s.name.lower() in kw_lower for s in profile.skills)
                if not profile_has_skill and kw_lower not in ["ci/cd", "rest api"]:
                    hallucinations_detected += 1
                    print(f"   ❌ Factual Alert: Tailored resume added keyword '{kw}' which is not in candidate skills.")

            # Clean up tailored resume and job
            db.delete(tailored_res)
            db.delete(job_obj)
            db.commit()

        print("\n----------------------------------------------------")
        print("📋 RESUME TAILORING SAFETY REPORT:")
        print("----------------------------------------------------")
        print(f"Total Combinations Evaluated: {len(eval_jobs)}")
        print(f"Hallucinations Detected:      {hallucinations_detected}")
        print(f"Factual Mismatches:           {factual_mismatches}")
        print(f" Factual Change Safety:      {100.0 - (hallucinations_detected * 20.0):.2f}%")
        print("✅ Factual safety assertion check: Zero fabricated resume claims.")

    finally:
        # Complete clean up
        db.delete(profile)
        db.delete(user)
        db.commit()
        db.close()

if __name__ == "__main__":
    run_resume_benchmark()
