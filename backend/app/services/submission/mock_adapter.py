import time
import uuid
from typing import Dict, Any, Optional
from app.services.submission.base import SubmissionAdapter, SubmissionState, SubmissionStateMachine


class MockSubmissionAdapter(SubmissionAdapter):
    """
    Mock Submission Adapter submitting applications to local mock application environment.
    Simulates verification checks, submission confirmation IDs, and human intervention pauses.
    """

    def __init__(self):
        self.state = SubmissionState.NOT_STARTED
        self.result = {}

    def transition_to(self, new_state: str):
        SubmissionStateMachine.validate_transition(self.state, new_state)
        self.state = new_state

    def can_submit(self, application_data: Dict[str, Any]) -> bool:
        job_url = application_data.get("job_url", "")
        return True

    def prepare(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        self.transition_to(SubmissionState.PREPARING)
        
        # Check for simulated mock human intervention trigger (e.g. mock CAPTCHA)
        if application_data.get("trigger_mock_captcha"):
            self.transition_to(SubmissionState.PAUSED)
            return {
                "success": False,
                "paused": True,
                "reason": "HUMAN_INTERVENTION_REQUIRED: Simulated CAPTCHA detected."
            }

        self.transition_to(SubmissionState.READY)
        return {"success": True, "state": self.state}

    def submit(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.state != SubmissionState.READY:
            raise ValueError(f"Cannot submit when adapter state is '{self.state}'. Expected READY.")

        self.transition_to(SubmissionState.SUBMITTING)
        time.sleep(0.05)  # Simulate network latency

        # Generate synthetic submission ID
        submission_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
        confirmation_msg = f"Application successfully submitted to mock portal for {application_data.get('job_title', 'Target Role')} at {application_data.get('company_name', 'Target Company')}."

        self.result = {
            "submission_id": submission_id,
            "confirmation": confirmation_msg,
            "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.transition_to(SubmissionState.VERIFYING)
        return self.result

    def verify_submission(self, result_data: Dict[str, Any]) -> bool:
        if self.state != SubmissionState.VERIFYING:
            return False

        # Verify presence of submission ID and confirmation message
        sub_id = result_data.get("submission_id")
        conf = result_data.get("confirmation")

        if sub_id and conf and sub_id.startswith("SUB-"):
            self.transition_to(SubmissionState.SUBMITTED)
            return True
        else:
            self.transition_to(SubmissionState.FAILED)
            return False

    def get_result(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "result": self.result
        }
