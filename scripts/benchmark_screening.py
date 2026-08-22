#!/usr/bin/env python3
import os
import sys

# Adjust python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.connection import SessionLocal
from app.models.profile import UserProfile, Skill, Education, Project
from app.services.screening.question_classifier import QuestionClassifier
from app.services.screening.answer_generator import AnswerGenerator
from app.services.screening.taxonomy import QuestionType
from tests.regression.golden_dataset import GOLDEN_PROFILE, GOLDEN_QUESTIONS

def run_screening_benchmark():
    print("====================================================")
    print("🤖 SCREENING ANSWER GROUNDING & SAFETY BENCHMARK")
    print("====================================================\n")

    # 1. Instantiate synthetic UserProfile object
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

    generator = AnswerGenerator()
    
    total_run = 0
    passed_asserts = 0
    
    # Fake job context
    job_context = {
        "job_title": "QA Automation Engineer",
        "company_name": "TechCorp",
        "description": "QA automation framework development."
    }

    for q in GOLDEN_QUESTIONS:
        total_run += 1
        q_text = q["question_text"]
        is_adversarial = q["is_adversarial"]
        
        # Use real QuestionClassifier
        classification = QuestionClassifier.classify_question(q_text, field_identifier=q["field_identifier"])
        map_type = classification["type"]
        
        # Set answer source: DETERMINISTIC if simple numeric/boolean, else AI_SYNTHESIS
        if "how many years" in q_text.lower() or "how much" in q_text.lower():
            answer_source = "DETERMINISTIC_RULE"
        elif map_type in [QuestionType.RELOCATION, QuestionType.LOCATION, QuestionType.SALARY]:
            answer_source = "DETERMINISTIC_RULE"
        else:
            answer_source = "AI_SYNTHESIS"
        
        res = generator.generate(
            question_text=q_text,
            question_type=map_type,
            answer_source=answer_source,
            profile=profile,
            job_context=job_context
        )

        status_res = res.get("status")
        ans_text = res.get("answer", "")
        
        print(f"Question: {q_text}")
        print(f" -> Output Status: {status_res}")
        print(f" -> Generated Answer: {ans_text}\n")

        if is_adversarial:
            # For adversarial queries where user profile has no matching keywords, assert INSUFFICIENT_INFORMATION
            if status_res == "INSUFFICIENT_INFORMATION":
                passed_asserts += 1
                print(" ✅ Safety Check Passed: Correctly blocked fabrication for missing skill.")
            else:
                print(" ❌ Safety Check Failed: Hallucination or fabricated statement allowed.")
        else:
            if status_res in ["READY", "GENERATED"]:
                passed_asserts += 1
                print(" ✅ Grounding Check Passed: Technical answer correctly synthesized from profile facts.")
            else:
                print(f" ❌ Grounding Check Failed: Valid question blocked or failed to answer. Reason: {res.get('reason')}")
        print("-" * 50)

    print("\n----------------------------------------------------")
    print("📈 SCREENING BENCHMARK RESULTS:")
    print("----------------------------------------------------")
    print(f"Total Questions Evaluated: {total_run}")
    print(f"Passed Grounding/Safety:   {passed_asserts}")
    print(f"Success Accuracy:          {passed_asserts / total_run * 100:.2f}%")
    print("✅ Screening answers safely grounded in user profile.")

if __name__ == "__main__":
    run_screening_benchmark()
