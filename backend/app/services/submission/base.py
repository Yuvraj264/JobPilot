from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SubmissionState:
    NOT_STARTED = "NOT_STARTED"
    PREPARING = "PREPARING"
    READY = "READY"
    SUBMITTING = "SUBMITTING"
    VERIFYING = "VERIFYING"
    SUBMITTED = "SUBMITTED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"


VALID_TRANSITIONS = {
    SubmissionState.NOT_STARTED: [SubmissionState.PREPARING, SubmissionState.FAILED],
    SubmissionState.PREPARING: [SubmissionState.READY, SubmissionState.FAILED, SubmissionState.PAUSED],
    SubmissionState.READY: [SubmissionState.SUBMITTING, SubmissionState.FAILED, SubmissionState.PAUSED],
    SubmissionState.SUBMITTING: [SubmissionState.VERIFYING, SubmissionState.FAILED, SubmissionState.PAUSED],
    SubmissionState.VERIFYING: [SubmissionState.SUBMITTED, SubmissionState.FAILED, SubmissionState.PAUSED],
    SubmissionState.SUBMITTED: [],
    SubmissionState.PAUSED: [SubmissionState.PREPARING, SubmissionState.READY, SubmissionState.FAILED],
    SubmissionState.FAILED: [SubmissionState.PREPARING]
}


class SubmissionStateMachine:
    """
    Submission State Machine enforcing valid state transitions.
    """

    @staticmethod
    def validate_transition(current_state: str, new_state: str) -> bool:
        allowed = VALID_TRANSITIONS.get(current_state, [])
        if new_state not in allowed:
            raise ValueError(f"INVALID SUBMISSION STATE TRANSITION: Cannot transition from '{current_state}' to '{new_state}'. Allowed: {allowed}")
        return True


class SubmissionAdapter(ABC):
    """
    Abstract Submission Adapter interface for platform submission targets.
    """

    @abstractmethod
    def can_submit(self, application_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def prepare(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def submit(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def verify_submission(self, result_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def get_result(self) -> Dict[str, Any]:
        pass
