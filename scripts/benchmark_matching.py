#!/usr/bin/env python3
import os
import sys

# Adjust python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.connection import SessionLocal
from app.models.profile import UserProfile, Skill, Education, Project
from app.models.job import Job
from app.models.matching import MatchConfig
from app.services.matching.scoring_engine import ScoringEngine
from tests.regression.golden_dataset import GOLDEN_PROFILE, get_synthetic_jobs

def run_matching_benchmark():
    print("====================================================")
    print("📊 JOB MATCHING ENGINE BENCHMARK SUITE")
    print("====================================================\n")

    db = SessionLocal()
    
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

    # Create dummy MatchConfig
    config = MatchConfig(
        weight_skills=0.35,
        weight_role=0.20,
        weight_experience=0.15,
        weight_location=0.10,
        weight_workplace=0.05,
        weight_employment=0.05,
        weight_education=0.05,
        weight_semantic=0.05,
        threshold_apply=85.0,
        threshold_review=70.0
    )

    # 2. Get synthetic jobs
    jobs = get_synthetic_jobs()
    print(f"Loaded {len(jobs)} synthetic benchmark jobs descriptions.")

    # 3. Evaluate matching
    tp, fp, tn, fn = 0, 0, 0, 0
    scores = []
    
    for sj in jobs:
        # Create temporary SQLAlchemy Job object
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
        
        # Evaluate
        eval_res = ScoringEngine.evaluate_job(profile, job_obj, config)
        overall_score = eval_res["overall_score"]
        recommendation = eval_res["recommendation"]
        scores.append(overall_score)

        expected = sj["expected_label"]
        
        # Binary classification mapping: GOOD_MATCH / POSSIBLE_MATCH -> Positive, POOR_MATCH -> Negative
        is_actual_positive = expected in ["GOOD_MATCH", "POSSIBLE_MATCH"]
        is_pred_positive = recommendation in ["APPLY", "REVIEW"]

        if is_actual_positive and is_pred_positive:
            tp += 1
        elif not is_actual_positive and is_pred_positive:
            fp += 1
        elif not is_actual_positive and not is_pred_positive:
            tn += 1
        elif is_actual_positive and not is_pred_positive:
            fn += 1

    # 4. Calculate metrics
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n----------------------------------------------------")
    print("📈 MATCHING PERFORMANCE REPORT:")
    print("----------------------------------------------------")
    print(f"Total Jobs Evaluated:   {total}")
    print(f"True Positives (TP):    {tp}")
    print(f"False Positives (FP):   {fp}")
    print(f"True Negatives (TN):    {tn}")
    print(f"False Negatives (FN):   {fn}")
    print(f"Accuracy:               {accuracy * 100:.2f}%")
    print(f"Precision:              {precision * 100:.2f}%")
    print(f"Recall:                 {recall * 100:.2f}%")
    print(f"F1-Score:               {f1_score * 100:.2f}%")
    
    # Match Calibration analysis
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    print(f"Average Score Spread:   {min_score:.1f}% to {max_score:.1f}% (Avg: {avg_score:.1f}%)")

    # Output calibration check
    print("\n----------------------------------------------------")
    print("🔍 CALIBRATION AUDIT:")
    print("----------------------------------------------------")
    if fp > 5:
        print("⚠️ Warning: High False Positive rate detected. Consider tightening hard eligibility or skill matching rules.")
    else:
        print("✅ Matching engine successfully rejected misaligned jobs with zero-fabricated experience.")

    db.close()

if __name__ == "__main__":
    run_matching_benchmark()
