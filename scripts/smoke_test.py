#!/usr/bin/env python3
import os
import sys
from fastapi.testclient import TestClient

# Adjust python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app.main import app
    from app.database.connection import SessionLocal
    from app.models import User, UserProfile, Job, JobMatch, Application, ApplicationPackage, TailoredResume, ApplicationQuestion, ApplicationAnswer
except ImportError as e:
    print(f"❌ Python path error: {str(e)}")
    sys.exit(1)

def run_smoke_test():
    print("====================================================")
    print("🚀 JOBPILOT LAUNCH SMOKE TEST ENGINE")
    print("====================================================\n")

    client = TestClient(app)
    db = SessionLocal()
    
    steps = {
        "1. Health Check Endpoint": False,
        "2. Demo Data Seeder Integration": False,
        "3. Profile Completeness Calculations": False,
        "4. Match Explanation Retrieval": False,
        "5. Resume Tailoring Validation": False,
        "6. Screening Question Extraction": False,
        "7. Application Package Assembly": False,
        "8. Human Review Approval Action": False,
        "9. Submission Authorization Token": False,
        "10. Mock Adapter Submission Run": False,
        "11. Analytics Aggregation compilation": False,
        "12. Demo Isolation & Reset Flow": False,
    }

    try:
        # Step 1: Health Check
        print("🔍 Checking Backend Server Health...")
        res = client.get("/health")
        if res.status_code == 200 and res.json()["status"] == "healthy":
            steps["1. Health Check Endpoint"] = True
            print("   ✅ Health endpoint is responsive and Database is connected.")
        else:
            print("   ❌ Health endpoint returned error.")
            return False

        # Step 2: Seed Demo Data
        print("\n🔍 Seeding complete synthetic Demo sandbox...")
        res = client.post("/api/demo/reset")
        if res.status_code == 200 and res.json()["success"]:
            steps["2. Demo Data Seeder Integration"] = True
            print("   ✅ Demo reset completed successfully.")
            db.close()
            db = SessionLocal()
        else:
            print("   ❌ Demo reset failed.")
            return False

        # Query demo profile details
        profile = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
        if not profile:
            print("   ❌ Demo UserProfile record missing in DB.")
            return False

        # Step 3: Profile Completeness
        print("\n🔍 Fetching Profile Completeness metrics...")
        res = client.get("/api/profile/completeness", headers={"X-User-Id": "99999"})
        if res.status_code == 200 and "percentage" in res.json():
            steps["3. Profile Completeness Calculations"] = True
            print(f"   ✅ Calculated Completeness: {res.json()['percentage']}%")
        else:
            print("   ❌ Failed to get profile completeness.")

        # Step 4: Job Matching and explanation
        print("\n🔍 Retrieving Job Match explanations...")
        demo_job = db.query(Job).filter(Job.title == "Senior QA Automation Engineer").first()
        if demo_job:
            res = client.get(f"/api/matching/job/{demo_job.id}", headers={"X-User-Id": "99999"})
            if res.status_code == 200 and "overall_score" in res.json():
                steps["4. Match Explanation Retrieval"] = True
                print(f"   ✅ Job Match explanation retrieved. Match Score: {res.json()['overall_score']}%")
            else:
                print("   ❌ Match evaluation endpoint failed.")
        else:
            print("   ❌ Demo job not found.")

        # Step 5: Resume Tailoring
        print("\n🔍 Inspecting Tailored Resumes...")
        res = client.get("/api/tailored-resumes", headers={"X-User-Id": "99999"})
        if res.status_code == 200 and len(res.json()) > 0:
            steps["5. Resume Tailoring Validation"] = True
            print(f"   ✅ Found {len(res.json())} tailored resumes associated with demo profile.")
        else:
            print("   ❌ Tailored resume search failed.")

        # Step 6: Screening Questions review queue
        print("\n🔍 Accessing Screening Questions review queue...")
        res = client.get("/api/questions/review", headers={"X-User-Id": "99999"})
        if res.status_code == 200:
            steps["6. Screening Question Extraction"] = True
            print(f"   ✅ Retrieved {len(res.json())} pending screening questions from review queue.")
        else:
            print("   ❌ Questions review queue returned error.")

        # Step 7: Application Package details
        print("\n🔍 Checking Application Packages...")
        res = client.get("/api/application-packages", headers={"X-User-Id": "99999"})
        if res.status_code == 200 and len(res.json()) > 0:
            steps["7. Application Package Assembly"] = True
            pkg_id = res.json()[0]["id"]
            print(f"   ✅ Found package #{pkg_id} ready for review.")
        else:
            print("   ❌ Application package listing failed.")
            return False

        # Step 8: App review and approve
        print("\n🔍 Approving application package...")
        db.close()
        db = SessionLocal()
        profile = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
        
        demo_app = db.query(Application).filter(Application.profile_id == profile.id, Application.status == "REVIEW").first()
        if demo_app:
            # First approve any pending screening questions to pass validation checks
            pending_q = db.query(ApplicationQuestion).join(ApplicationAnswer).filter(
                ApplicationQuestion.job_id == demo_app.job_id,
                ApplicationAnswer.answer_status == "NEEDS_REVIEW"
            ).first()
            if pending_q:
                print(f"   ℹ️ Approving pending screening question: '{pending_q.question_text[:40]}...'")
                q_res = client.post(
                    f"/api/questions/{pending_q.id}/approve",
                    headers={"X-User-Id": "99999"},
                    json={"answer_text": "I am excited to join TechGiant Inc.", "save_to_memory": True}
                )
                if q_res.status_code != 200:
                    print(f"   ❌ Question approval failed: {q_res.json()}")
                db.close()
                db = SessionLocal()
                demo_app = db.query(Application).filter(Application.profile_id == profile.id, Application.status == "REVIEW").first()
            else:
                print("   ℹ️ No pending screening questions found.")
        else:
            print("   ❌ Demo application not found in Step 8.")
        if demo_app:
            res = client.post(
                f"/api/applications/{demo_app.id}/approve",
                headers={"X-User-Id": "99999"},
                json={"user_confirmed": True, "notes": "Approved in smoke test"}
            )
            if res.status_code == 200 and res.json()["status"] == "APPROVED":
                steps["8. Human Review Approval Action"] = True
                print("   ✅ Application approved and transitioned to APPROVED.")
            else:
                print(f"   ❌ Approval failed. Status code: {res.status_code}, detail: {res.json().get('detail')}")
        else:
            print("   ❌ App requiring review not found.")

        # Step 9: Authorize application submission
        print("\n🔍 Issuing Submission Authorization Token...")
        if demo_app:
            res = client.post(f"/api/applications/{demo_app.id}/authorize-submission", headers={"X-User-Id": "99999"})
            if res.status_code == 200:
                steps["9. Submission Authorization Token"] = True
                print("   ✅ Submission token successfully issued.")
            else:
                print("   ❌ Submission authorization failed.")
        else:
            print("   ❌ App for authorization not found.")

        # Step 10: Mock Adapter Execution
        print("\n🔍 Executing Mock Platform submission run...")
        if demo_app:
            res = client.post(f"/api/applications/{demo_app.id}/submit", headers={"X-User-Id": "99999"})
            if res.status_code == 200:
                steps["10. Mock Adapter Submission Run"] = True
                print("   ✅ Mock submission execution run initiated.")
            else:
                print("   ❌ Submission run trigger failed.")
        else:
            print("   ❌ App for execution not found.")

        # Step 11: Analytics Overview
        print("\n🔍 Verifying Analytics Compile pipeline...")
        res = client.get("/api/analytics/overview", headers={"X-User-Id": "99999"})
        if res.status_code == 200:
            steps["11. Analytics Aggregation compilation"] = True
            print("   ✅ Analytics dashboard compiles successfully.")
        else:
            print("   ❌ Overview analytics returned error.")

        # Step 12: Clear & Reset Demo Mode
        print("\n🔍 Running Reset Demo sequence...")
        res = client.post("/api/demo/reset")
        if res.status_code == 200:
            # Verify demo data matches are re-seeded correctly
            profile_after = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
            if profile_after:
                steps["12. Demo Isolation & Reset Flow"] = True
                print("   ✅ Demo reset cleans and seeds correctly.")
            else:
                print("   ❌ Profile re-seeding failed after reset.")
        else:
            print("   ❌ Demo reset endpoint failed.")

    except Exception as err:
        print(f"\n❌ Exception occurred during smoke test run: {str(err)}")
        return False
    finally:
        db.close()

    print("\n====================================================")
    print("📋 LAUNCH VALIDATION SUMMARY")
    print("====================================================")
    all_ok = True
    for step_name, status in steps.items():
        icon = "✅" if status else "❌"
        print(f" {icon} {step_name}")
        if not status:
            all_ok = False

    print("\n====================================================")
    if all_ok:
        print("🎉 JOBPILOT IS LAUNCH READY! ALL SMOKE TESTS PASSED.")
        print("====================================================")
        return True
    else:
        print("🚨 LAUNCH BLOCKED: SOME SMOKE TESTS FAILED.")
        print("====================================================")
        return False

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
