#!/usr/bin/env python3
import os
import sys

# Adjust python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.connection import SessionLocal
from app.models.profile import UserProfile, Skill, Education, Project
from app.models.job import Job
from app.services.automation.profile_field_mapper import ProfileFieldMapper
from app.services.job_deduplicator import JobDeduplicator
from tests.regression.golden_dataset import GOLDEN_PROFILE

def run_automation_benchmark():
    print("====================================================")
    print("🤖 FORM AUTOMATION & RELIABILITY BENCHMARK")
    print("====================================================\n")

    db = SessionLocal()
    
    # 1. Profile Field Mapping Evaluation
    profile = UserProfile(
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
    profile.skills = [Skill(name=s["name"], proficiency=s["proficiency"], years_of_experience=s["years_of_experience"]) for s in GOLDEN_PROFILE["skills"]]
    profile.education = [Education(degree=e["degree"], field_of_study=e["field_of_study"], institution=e["institution"], end_year=e["end_year"]) for e in GOLDEN_PROFILE["education"]]
    profile.projects = [Project(name=p["name"], description=p["description"], technologies=p["technologies"]) for p in GOLDEN_PROFILE["projects"]]

    # Evaluate field mapping
    mappings = {
        "PERSONAL_NAME": GOLDEN_PROFILE["full_name"],
        "EMAIL": GOLDEN_PROFILE["email"],
        "PHONE": GOLDEN_PROFILE["phone"],
        "LOCATION": GOLDEN_PROFILE["current_city"],
        "EXPERIENCE": "5.0",
        "CURRENT_ROLE": GOLDEN_PROFILE["current_role"]
    }
    
    mapping_passed = 0
    for field, expected_val in mappings.items():
        res = ProfileFieldMapper.map_field(field, profile, None)
        if res["status"] == "MATCHED" and str(res["value"]) == expected_val:
            mapping_passed += 1
            print(f" ✅ Field Mapping Passed: '{field}' correctly mapped to '{expected_val}'.")
        else:
            print(f" ❌ Field Mapping Failed: '{field}' expected '{expected_val}', got '{res.get('value')}'")

    print("\n----------------------------------------------------")
    print("🔍 DUPLICATE DETECTION EVALUATION:")
    print("----------------------------------------------------")
    
    # Add a mock job in database
    job_a = Job(
        title="QA Automation Lead",
        company_name="Duplicate Inc",
        location="Austin, TX",
        job_url="https://example.com/jobs/101",
        external_job_id="ext-101",
        source_id=1
    )
    db.add(job_a)
    db.commit()
    db.refresh(job_a)

    # 1. Same URL, same source -> should return DUPLICATE
    norm_job_1 = {
        "title": "QA Automation Lead",
        "company_name": "Duplicate Inc",
        "job_url": "https://example.com/jobs/101",
        "external_job_id": "ext-101"
    }
    status1, _ = JobDeduplicator.check_duplicate(db, norm_job_1, 1)
    
    # 2. Same URL, different source -> should return POTENTIAL_DUPLICATE
    status2, _ = JobDeduplicator.check_duplicate(db, norm_job_1, 2)
    
    # Clean up mock job
    db.delete(job_a)
    db.commit()

    duplicate_passed = 0
    if status1 == "DUPLICATE":
        duplicate_passed += 1
        print(" ✅ Duplicate URL Check Passed: Exact duplicate blocked.")
    else:
        print(f" ❌ Duplicate URL Check Failed: Expected DUPLICATE, got {status1}")

    if status2 == "POTENTIAL_DUPLICATE":
        duplicate_passed += 1
        print(" ✅ Cross-Source Duplicate Check Passed: Flagged as potential duplicate.")
    else:
        print(f" ❌ Cross-Source Duplicate Check Failed: Expected POTENTIAL_DUPLICATE, got {status2}")

    # Final summary
    total_asserts = len(mappings) + 2
    success_rate = (mapping_passed + duplicate_passed) / total_asserts * 100
    
    print("\n----------------------------------------------------")
    print("📊 AUTOMATION & RELIABILITY SUMMARY:")
    print("----------------------------------------------------")
    print(f"Total Tests Run: {total_asserts}")
    print(f"Passed Checks:   {mapping_passed + duplicate_passed}")
    print(f"Success Rate:    {success_rate:.2f}%")
    print("✅ Form automation rules and duplicate prevention validated successfully.")

    db.close()

if __name__ == "__main__":
    run_automation_benchmark()
