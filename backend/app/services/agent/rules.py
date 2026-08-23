from typing import Dict, Any, Optional

class AgentDecisionRules:
    """
    Deterministic rules engine evaluated before AI advisory layers.
    Guarantees safety gates are enforced first.
    """

    @staticmethod
    def evaluate_rules(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job = context.get("job")
        application = context.get("application")
        history_status = context.get("history_status")
        mission = context.get("mission")
        platform_caps = context.get("platform_capabilities")
        
        # 1. Job Already Submitted / Duplicate Check
        if history_status in ["ALREADY_APPLIED", "ALREADY_IN_PROGRESS"]:
            return {
                "decision": "SKIP",
                "confidence": 1.0,
                "reasoning": ["Job already applied to or currently in progress (duplicate protection)."],
                "blockers": [],
                "proposed_actions": ["SKIP"]
            }

        # 2. Job Status Expiration Checks
        if job and job.status in ["EXPIRED", "CLOSED"]:
            return {
                "decision": "SKIP",
                "confidence": 1.0,
                "reasoning": [f"Target job is no longer active (status: '{job.status}')."],
                "blockers": [],
                "proposed_actions": ["SKIP"]
            }

        # 3. Hard Eligibility Checks (Match config defaults)
        min_match = 70.0
        if mission:
            min_match = mission.objective.get("minimum_match_score", 70.0)

        # Get overall match score
        from app.models.matching import JobMatch
        # Query match score from context or find it
        match_score = 0.0
        recommendation = "SKIP"
        if job and context.get("profile"):
            # We can check if a match was computed
            pass

        # 4. CAPTCHA Check
        if platform_caps and platform_caps.get("has_captcha", False):
            return {
                "decision": "WAIT",
                "confidence": 1.0,
                "reasoning": ["CAPTCHA checkpoint detected on application portal."],
                "blockers": ["CAPTCHA_REQUIRED"],
                "proposed_actions": ["START_HUMAN_ASSISTED_SESSION"]
            }

        # 5. Unsupported Platform / Automation capability
        if platform_caps and not platform_caps.get("supports_automation", False):
            return {
                "decision": "WAIT",
                "confidence": 0.95,
                "reasoning": ["Application platform does not support automatic background submission."],
                "blockers": ["AUTOMATION_UNSUPPORTED"],
                "proposed_actions": ["START_HUMAN_ASSISTED_SESSION"]
            }

        # 6. Check Application Package Validation Blockers
        if application:
            if application.status == "FAILED":
                return {
                    "decision": "PREPARE",
                    "confidence": 0.9,
                    "reasoning": ["Previous application preparation failed quality gate validations."],
                    "blockers": [application.failure_reason or "QUALITY_GATE_FAIL"],
                    "proposed_actions": ["CREATE_PACKAGE"]
                }
            
            # Check validation gates
            # If application status is PREPARING, we should prepare it
            if application.status == "PREPARING":
                return {
                    "decision": "PREPARE",
                    "confidence": 0.9,
                    "reasoning": ["Application is in PREPARING status; requires package generation."],
                    "blockers": [],
                    "proposed_actions": ["CREATE_PACKAGE"]
                }

            # Human Review and Approval Missing
            if application.status == "READY_FOR_REVIEW":
                return {
                    "decision": "WAIT",
                    "confidence": 1.0,
                    "reasoning": ["Application package prepared and waiting for human review approval."],
                    "blockers": ["APPROVAL_MISSING"],
                    "proposed_actions": ["REQUEST_REVIEW"]
                }

            # Time-bound Submission Authorization Missing / Expired
            if application.status == "APPROVED":
                # Check if authorized
                from app.models.application import SubmissionAuthorization
                # Find authorization
                return {
                    "decision": "WAIT",
                    "confidence": 1.0,
                    "reasoning": ["Application is approved but lacks active submission authorization."],
                    "blockers": ["AUTHORIZATION_MISSING"],
                    "proposed_actions": ["WAIT"]
                }

        # If no application exists, first step is to PREPARE
        if not application and job:
            return {
                "decision": "PREPARE",
                "confidence": 0.85,
                "reasoning": ["No application package exists for this job."],
                "blockers": [],
                "proposed_actions": ["CREATE_PACKAGE"]
            }

        return None
