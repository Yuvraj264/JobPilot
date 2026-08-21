from typing import List, Dict, Any, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.automation.form_analyzer import FormAnalyzer
from app.services.automation.profile_field_mapper import ProfileFieldMapper


class ApplicationActionPlanner:
    """
    Action Planner producing validated sequence of structured browser actions.
    Emits PAUSE_FOR_HUMAN when fields require reasoning, data is missing, or CAPTCHA is detected.
    """

    @staticmethod
    def plan_page_actions(
        inspection_data: Dict[str, Any],
        profile: UserProfile,
        default_resume: Optional[Resume] = None,
        confidence_threshold: float = 0.80
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

        for el in elements:
            sem_type = FormAnalyzer.classify_field(el)
            mapping = ProfileFieldMapper.map_field(sem_type, profile, default_resume)
            conf = mapping["confidence"]
            val = mapping["value"]
            status = mapping["status"]

            # Trigger Pause if Screening Question or Missing Required Profile Data
            if status == "REQUIRES_REASONING":
                pause_reasons.append(f"Screening question detected ('{el.get('label')}') requiring human reasoning.")
                continue

            if el.get("required") and status == "MISSING_DATA":
                pause_reasons.append(f"Required profile data missing for field '{el.get('label')}' ({sem_type}).")
                continue

            if conf < confidence_threshold:
                pause_reasons.append(f"Low confidence ({conf}) for field '{el.get('label')}'.")
                continue

            # Build Validated Action
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
