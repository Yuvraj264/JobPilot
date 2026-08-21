import pytest
from app.services.submission.base import SubmissionState, SubmissionStateMachine


def test_valid_submission_state_transitions():
    assert SubmissionStateMachine.validate_transition(SubmissionState.NOT_STARTED, SubmissionState.PREPARING)
    assert SubmissionStateMachine.validate_transition(SubmissionState.PREPARING, SubmissionState.READY)
    assert SubmissionStateMachine.validate_transition(SubmissionState.READY, SubmissionState.SUBMITTING)
    assert SubmissionStateMachine.validate_transition(SubmissionState.SUBMITTING, SubmissionState.VERIFYING)
    assert SubmissionStateMachine.validate_transition(SubmissionState.VERIFYING, SubmissionState.SUBMITTED)


def test_invalid_submission_state_transitions():
    with pytest.raises(ValueError, match="INVALID SUBMISSION STATE TRANSITION"):
        SubmissionStateMachine.validate_transition(SubmissionState.NOT_STARTED, SubmissionState.SUBMITTED)

    with pytest.raises(ValueError, match="INVALID SUBMISSION STATE TRANSITION"):
        SubmissionStateMachine.validate_transition(SubmissionState.SUBMITTED, SubmissionState.SUBMITTING)
