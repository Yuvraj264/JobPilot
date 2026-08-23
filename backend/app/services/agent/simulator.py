from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.agent.context import AgentContextBuilder
from app.services.agent.rules import AgentDecisionRules
from app.services.agent.policy import AgentPolicyEngine


class DecisionSimulator:
    """
    Simulates a dry-run step of the context-rules-policy cycle without executing side effects.
    """

    @staticmethod
    def simulate_decision(
        db: Session,
        profile_id: int,
        job_id: int,
        mission_id: Optional[int] = None
    ) -> Dict[str, Any]:
        # 1. Build dry-run context
        context = AgentContextBuilder.build_context(db, profile_id, job_id, mission_id)

        # 2. Candidate Action Generation
        possible_actions = ["SKIP"]
        if context.get("job"):
            possible_actions.extend(["CREATE_PACKAGE", "REQUEST_REVIEW", "EXECUTE_PERMITTED_APPLICATION", "START_HUMAN_ASSISTED_SESSION"])

        # 3. Rules Evaluation
        rules_plan = AgentDecisionRules.evaluate_rules(context)
        
        decision = "SKIP"
        confidence = 0.5
        reasoning = ["No matching rules met; defaulted to SKIP."]
        proposed_actions = ["SKIP"]

        if rules_plan:
            decision = rules_plan["decision"]
            confidence = rules_plan["confidence"]
            reasoning = rules_plan["reasoning"]
            proposed_actions = rules_plan["proposed_actions"]

        # 4. Dry-run Policy Validation on proposed actions
        policy_checks = {}
        for action in proposed_actions:
            status, reason = AgentPolicyEngine.validate_action(db, profile_id, action, job_id, mission_id)
            policy_checks[action] = {"status": status, "reason": reason}

        # 5. Determine final action
        final_action = "SKIP"
        for action in proposed_actions:
            if policy_checks.get(action, {}).get("status") == "ALLOWED":
                final_action = action
                break

        return {
            "context_snapshot": context.get("snapshot"),
            "possible_actions": possible_actions,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "proposed_actions": proposed_actions,
            "policy_checks": policy_checks,
            "final_action": final_action
        }
