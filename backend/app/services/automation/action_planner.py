from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.automation.form_analyzer import FormAnalyzer
from app.services.automation.profile_field_mapper import ProfileFieldMapper
from app.services.screening.question_processing_service import QuestionProcessingService


class ApplicationActionPlanner:
    """
    Action Planner producing validated sequence of structured browser actions.
    Integrates Phase 7 Question Processing Service for screening question evaluation.
    Emits PAUSE_FOR_HUMAN when questions require human review or data is missing.
    """

    @staticmethod
    def plan_page_actions(
        inspection_data: Dict[str, Any],
        profile: UserProfile,
        default_resume: Optional[Resume] = None,
        confidence_threshold: float = 0.80,
        db: Optional[Session] = None,
        automation_run_id: Optional[int] = None,
        job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        
        # 1. Check CAPTCHA Presence
        if inspection_data.get("has_captcha"):
            return {
                "automatable": False,
                "pause_reason": "Mock CAPTCHA challenge widget detected on page.",
                "actions": [{"action": "PAUSE_FOR_HUMAN", "reason": "CAPTCHA_DETECTED"}]
            }

        elements = inspection_data.get("elements", [])
        if not elements:
            return {
                "automatable": True,
                "actions": []
            }

        actions: List[Dict[str, Any]] = []
        pause_reasons: List[str] = []
        processor = QuestionProcessingService()

        for el in elements:
            sem_type = FormAnalyzer.classify_field(el)

            # Phase 7 Screening Question Processing
            if sem_type == "SCREENING_QUESTION" or el.get("tag_name") == "textarea":
                q_text = el.get("label") or el.get("placeholder") or "Screening Question"
                
                if db:
                    job_ctx = {"title": "Target Role", "company_name": "Target Company"}
                    res_q = processor.process_question(
                        db=db,
                        question_text=q_text,
                        profile=profile,
                        job_context=job_ctx,
                        automation_run_id=automation_run_id,
                        job_id=job_id,
                        field_identifier=el.get("id") or el.get("name"),
                        required=el.get("required", True),
                        resume=default_resume,
                        require_human_review=True  # Require human review per Phase 7 safety rule
                    )

                    if res_q.get("requires_human") or res_q.get("status") in ["NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"]:
                        pause_reasons.append(f"Screening question requiring human review: '{q_text}' ({res_q.get('reason') or 'Review required'}).")
                        continue
                    else:
                        actions.append({
                            "action": "FILL",
                            "field_type": "SCREENING_QUESTION",
                            "element": el,
                            "value": res_q.get("answer_text"),
                            "confidence": res_q.get("confidence", 0.90)
                        })
                        continue
                else:
                    pause_reasons.append(f"Screening question detected ('{q_text}') requiring human reasoning.")
                    continue

            # Standard Profile Field Mapping
            mapping = ProfileFieldMapper.map_field(sem_type, profile, default_resume)
            conf = mapping["confidence"]
            val = mapping["value"]
            status = mapping["status"]

            if el.get("required") and status == "MISSING_DATA":
                pause_reasons.append(f"Required profile data missing for field '{el.get('label')}' ({sem_type}).")
                continue

            if conf < confidence_threshold:
                pause_reasons.append(f"Low confidence ({conf}) for field '{el.get('label')}'.")
                continue

            tag = el.get("tag_name")
            input_type = el.get("input_type")

            if input_type == "file" or sem_type == "RESUME":
                actions.append({
                    "action": "UPLOAD",
                    "field_type": sem_type,
                    "element": el,
                    "value": val,
                    "confidence": conf
                })
            elif tag == "select":
                actions.append({
                    "action": "SELECT",
                    "field_type": sem_type,
                    "element": el,
                    "value": val,
                    "confidence": conf
                })
            elif input_type in ["radio", "checkbox"]:
                actions.append({
                    "action": "CHECK",
                    "field_type": sem_type,
                    "element": el,
                    "value": val,
                    "confidence": conf
                })
            else:
                actions.append({
                    "action": "FILL",
                    "field_type": sem_type,
                    "element": el,
                    "value": val,
                    "confidence": conf
                })

        if pause_reasons:
            return {
                "automatable": False,
                "pause_reason": " | ".join(pause_reasons),
                "actions": actions + [{"action": "PAUSE_FOR_HUMAN", "reasons": pause_reasons}]
            }

        return {
            "automatable": True,
            "actions": actions
        }
