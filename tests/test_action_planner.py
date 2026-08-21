import pytest
from app.models.profile import UserProfile
from app.services.automation.action_planner import ApplicationActionPlanner


def test_action_planner_captcha_and_screening():
    profile = UserProfile(full_name="Jane Doe", email="jane@example.com")

    # 1. CAPTCHA pause
    plan_cap = ApplicationActionPlanner.plan_page_actions({"has_captcha": True}, profile)
    assert plan_cap["automatable"] is False
    assert "CAPTCHA" in plan_cap["pause_reason"]

    # 2. Screening Question pause
    plan_screen = ApplicationActionPlanner.plan_page_actions(
        {
            "has_captcha": False,
            "elements": [
                {"tag_name": "textarea", "label": "Why are you interested in this role?", "required": True}
            ]
        },
        profile
    )
    assert plan_screen["automatable"] is False
    assert "Screening question" in plan_screen["pause_reason"]
