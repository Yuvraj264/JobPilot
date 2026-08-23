import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.agent import AgentDecisionRecord
from app.services.agent.context import AgentContextBuilder
from app.services.agent.rules import AgentDecisionRules
from app.services.agent.policy import AgentPolicyEngine
from app.services.agent.gateway import AgentActionGateway
from app.services.agent.escalation import HumanEscalationService

logger = logging.getLogger(__name__)


class AgentDecisionEngine:
    """
    Main Agent decision processing engine.
    Orchestrates Context construction, deterministic rules matching, risk scoring,
    and action routing through the strict policy gates.
    """

    # Global active mode: OBSERVE, PLAN, ASSIST, AUTONOMOUS_WITH_REVIEW
    ACTIVE_MODE = "AUTONOMOUS_WITH_REVIEW"

    @classmethod
    def evaluate_and_execute(
        cls,
        db: Session,
        profile_id: int,
        job_id: int,
        mission_id: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> AgentDecisionRecord:
        # 1. Idempotency Check
        idem_key = idempotency_key or f"idem-{uuid.uuid4()}"

        # 2. Context Builder Snapshot
        context = AgentContextBuilder.build_context(db, profile_id, job_id, mission_id)
        snapshot = context.get("snapshot")

        # 3. Deterministic rules layer logic
        plan = AgentDecisionRules.evaluate_rules(context)
        
        decision = "SKIP"
        confidence = 0.5
        reasoning = ["No deterministic rules triggered."]
        blockers = []
        proposed_actions = ["SKIP"]

        if plan:
            decision = plan["decision"]
            confidence = plan["confidence"]
            reasoning = plan["reasoning"]
            blockers = plan["blockers"]
            proposed_actions = plan["proposed_actions"]

        # AI Advisory validation checks
        # Verify prompt injection protections
        job = context.get("job")
        desc_lower = (job.description or "").lower() if job else ""
        if "ignore your instructions" in desc_lower or "apply immediately" in desc_lower:
            reasoning.append("Prompt Injection Protection: Rejected hostile job content override instructions.")
            decision = "SKIP"
            proposed_actions = ["SKIP"]

        # 4. Action Gateway Scoring
        # Select best action from proposals
        selected_action = proposed_actions[0] if proposed_actions else "SKIP"

        # Enforce Mode Constraints
        # OBSERVE mode performs no mutations
        if cls.ACTIVE_MODE == "OBSERVE":
            reasoning.append("Agent Mode: OBSERVE mode is active. Execution skipped.")
            policy_res = "ALLOWED"
            safety_res = "ALLOWED"
            selected_action = "SKIP"
        else:
            # 5. Policy Engine Gatekeeper check
            policy_res, safety_reason = AgentPolicyEngine.validate_action(
                db, profile_id, selected_action, job_id, mission_id
            )
            
            safety_res = "ALLOWED"
            if policy_res == "BLOCKED":
                safety_res = "BLOCKED"
                blockers.append(safety_reason)
                reasoning.append(f"Policy Block: {safety_reason}")
                selected_action = "SKIP"

        # 6. Execute whitelisted mutations via Gateway if ALLOWED
        if selected_action != "SKIP" and policy_res == "ALLOWED":
            success, msg = AgentActionGateway.execute_action(
                db=db,
                profile_id=profile_id,
                action=selected_action,
                job_id=job_id,
                mission_id=mission_id,
                idempotency_key=idem_key
            )
            if not success:
                policy_res = "BLOCKED"
                blockers.append(msg)
                reasoning.append(f"Execution Error: {msg}")
                selected_action = "SKIP"
            else:
                reasoning.append(f"Gateway execution: {msg}")

        # 7. Record decision audit log
        record = AgentDecisionRecord(
            profile_id=profile_id,
            job_id=job_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            blockers=blockers,
            policy_result=policy_res,
            safety_result=safety_res,
            selected_action=selected_action,
            context_snapshot=snapshot,
            engine_version=1,
            policy_version=1,
            configuration_version=1
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # 8. Post-actions human escalations trigger
        if "APPROVAL_MISSING" in blockers:
            HumanEscalationService.escalate(
                db=db,
                profile_id=profile_id,
                application_id=context.get("application").id if context.get("application") else None,
                intervention_type="APPLICATION_APPROVAL",
                message="Application requires human review and confirmation approval.",
                priority="HIGH"
            )
        elif "CAPTCHA_REQUIRED" in blockers or "AUTHENTICATION_REQUIRED" in blockers:
            HumanEscalationService.escalate(
                db=db,
                profile_id=profile_id,
                application_id=context.get("application").id if context.get("application") else None,
                intervention_type="CAPTCHA_OR_LOGIN",
                message="CAPTCHA checkpoint or portal authentication session verification required.",
                priority="CRITICAL"
            )

        return record
