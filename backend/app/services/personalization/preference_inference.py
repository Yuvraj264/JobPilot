from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.personalization import (
    PersonalPreferenceProfile,
    PreferenceConfigurationVersion,
    BehavioralSignal,
    JobFeedback,
    OptimizationSuggestion,
    PreferenceFeedback
)
from app.models.job import Job


def get_or_create_preference_profile(db: Session, profile_id: int) -> PersonalPreferenceProfile:
    pref = db.query(PersonalPreferenceProfile).filter(PersonalPreferenceProfile.profile_id == profile_id).first()
    if not pref:
        pref = PersonalPreferenceProfile(
            profile_id=profile_id,
            enabled=True,
            answer_style="Concise",
            preferred_roles=[],
            disliked_roles=[],
            preferred_locations=[],
            excluded_locations=[],
            preferred_companies=[],
            excluded_companies=[],
            preferred_industries=[],
            excluded_industries=[],
            preferred_skills=[],
            disliked_skills=[],
            workplace_modes=[],
            employment_types=[],
            minimum_salary={},
            preferred_salary={}
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def log_config_version(db: Session, profile_id: int, changes: dict, source: str = None) -> PreferenceConfigurationVersion:
    latest = db.query(PreferenceConfigurationVersion).filter(
        PreferenceConfigurationVersion.profile_id == profile_id
    ).order_by(PreferenceConfigurationVersion.version.desc()).first()
    
    next_version = (latest.version + 1) if latest else 1
    
    pref = get_or_create_preference_profile(db, profile_id)
    snapshot = {
        "enabled": pref.enabled,
        "answer_style": pref.answer_style,
        "preferred_roles": pref.preferred_roles,
        "disliked_roles": pref.disliked_roles,
        "preferred_locations": pref.preferred_locations,
        "excluded_locations": pref.excluded_locations,
        "preferred_companies": pref.preferred_companies,
        "excluded_companies": pref.excluded_companies,
        "preferred_industries": pref.preferred_industries,
        "excluded_industries": pref.excluded_industries,
        "preferred_skills": pref.preferred_skills,
        "disliked_skills": pref.disliked_skills,
        "workplace_modes": pref.workplace_modes,
        "employment_types": pref.employment_types,
        "minimum_salary": pref.minimum_salary,
        "preferred_salary": pref.preferred_salary
    }
    
    version_rec = PreferenceConfigurationVersion(
        profile_id=profile_id,
        version=next_version,
        changes=changes,
        preferences_snapshot=snapshot,
        source=source
    )
    db.add(version_rec)
    db.commit()
    db.refresh(version_rec)
    return version_rec


def rollback_preference_config(db: Session, profile_id: int) -> bool:
    latest = db.query(PreferenceConfigurationVersion).filter(
        PreferenceConfigurationVersion.profile_id == profile_id
    ).order_by(PreferenceConfigurationVersion.version.desc()).first()
    
    if not latest:
        return False
        
    previous = db.query(PreferenceConfigurationVersion).filter(
        PreferenceConfigurationVersion.profile_id == profile_id,
        PreferenceConfigurationVersion.version < latest.version
    ).order_by(PreferenceConfigurationVersion.version.desc()).first()
    
    pref = get_or_create_preference_profile(db, profile_id)
    
    if previous:
        snapshot = previous.preferences_snapshot
    else:
        snapshot = {
            "enabled": True,
            "answer_style": "Concise",
            "preferred_roles": [],
            "disliked_roles": [],
            "preferred_locations": [],
            "excluded_locations": [],
            "preferred_companies": [],
            "excluded_companies": [],
            "preferred_industries": [],
            "excluded_industries": [],
            "preferred_skills": [],
            "disliked_skills": [],
            "workplace_modes": [],
            "employment_types": [],
            "minimum_salary": {},
            "preferred_salary": {}
        }
        
    pref.enabled = snapshot.get("enabled", True)
    pref.answer_style = snapshot.get("answer_style", "Concise")
    pref.preferred_roles = snapshot.get("preferred_roles", [])
    pref.disliked_roles = snapshot.get("disliked_roles", [])
    pref.preferred_locations = snapshot.get("preferred_locations", [])
    pref.excluded_locations = snapshot.get("excluded_locations", [])
    pref.preferred_companies = snapshot.get("preferred_companies", [])
    pref.excluded_companies = snapshot.get("excluded_companies", [])
    pref.preferred_industries = snapshot.get("preferred_industries", [])
    pref.excluded_industries = snapshot.get("excluded_industries", [])
    pref.preferred_skills = snapshot.get("preferred_skills", [])
    pref.disliked_skills = snapshot.get("disliked_skills", [])
    pref.workplace_modes = snapshot.get("workplace_modes", [])
    pref.employment_types = snapshot.get("employment_types", [])
    pref.minimum_salary = snapshot.get("minimum_salary", {})
    pref.preferred_salary = snapshot.get("preferred_salary", {})
    
    db.delete(latest)
    db.commit()
    return True


class PreferenceInferenceService:
    """
    Analyzes behavioral signals and direct job feedback to produce non-intrusive configuration optimization suggestions.
    """

    @classmethod
    def generate_suggestions(cls, db: Session, profile_id: int) -> List[OptimizationSuggestion]:
        # 1. Fetch personalization profile
        pref_profile = get_or_create_preference_profile(db, profile_id)
        if not pref_profile.enabled:
            return []

        suggestions = []

        # Analyze Workplace Mode (e.g. skips onsite roles)
        skips_onsite = db.query(JobFeedback).join(Job).filter(
            JobFeedback.profile_id == profile_id,
            JobFeedback.feedback_type == "Skip",
            JobFeedback.rejection_reason == "work mode",
            Job.workplace_type == "ONSITE"
        ).count()

        if skips_onsite >= 3:
            # Check if suggestion already exists
            exists = db.query(OptimizationSuggestion).filter(
                OptimizationSuggestion.profile_id == profile_id,
                OptimizationSuggestion.category == "work_mode",
                OptimizationSuggestion.status == "PENDING"
            ).first()
            if not exists:
                sug = OptimizationSuggestion(
                    profile_id=profile_id,
                    category="work_mode",
                    suggestion="You frequently skip onsite jobs. Would you like to exclude onsite roles from recommendations?",
                    evidence=f"Skipped {skips_onsite} onsite jobs explicitly due to workplace arrangement preferences.",
                    severity="MEDIUM",
                    status="PENDING",
                    proposed_changes={
                        "preference_key": "excluded_locations",
                        "action": "exclude_mode",
                        "value": "ONSITE"
                    }
                )
                db.add(sug)
                suggestions.append(sug)

        # Analyze Roles (e.g. saves QA Automation)
        saves_qa = db.query(JobFeedback).join(Job).filter(
            JobFeedback.profile_id == profile_id,
            JobFeedback.feedback_type == "Save",
            Job.title.ilike("%QA%Automation%")
        ).count()

        if saves_qa >= 3:
            exists = db.query(OptimizationSuggestion).filter(
                OptimizationSuggestion.profile_id == profile_id,
                OptimizationSuggestion.category == "role",
                OptimizationSuggestion.status == "PENDING"
            ).first()
            if not exists:
                sug = OptimizationSuggestion(
                    profile_id=profile_id,
                    category="role",
                    suggestion="You saved multiple QA Automation roles. Would you like to add QA Automation to your preferred roles?",
                    evidence=f"Saved {saves_qa} listings matching 'QA Automation'.",
                    severity="HIGH",
                    status="PENDING",
                    proposed_changes={
                        "preference_key": "preferred_roles",
                        "action": "add",
                        "value": "QA Automation"
                    }
                )
                db.add(sug)
                suggestions.append(sug)

        db.commit()
        # Return all pending suggestions
        return db.query(OptimizationSuggestion).filter(
            OptimizationSuggestion.profile_id == profile_id,
            OptimizationSuggestion.status == "PENDING"
        ).all()

    @classmethod
    def accept_suggestion(cls, db: Session, suggestion_id: int) -> bool:
        sug = db.query(OptimizationSuggestion).filter(OptimizationSuggestion.id == suggestion_id).first()
        if not sug or sug.status != "PENDING":
            return False

        pref = get_or_create_preference_profile(db, sug.profile_id)
        changes = sug.proposed_changes
        key = changes.get("preference_key")
        action = changes.get("action")
        val = changes.get("value")

        # Log configuration change version
        log_config_version(db, sug.profile_id, changes, source=f"SUGGESTION_{sug.id}")

        if key == "excluded_locations" and action == "exclude_mode":
            # Exclude workplace mode by adding to excluded config
            modes = list(pref.workplace_modes)
            # Find or append mode
            found = False
            for m in modes:
                if m.get("value") == val:
                    m["strength"] = 1.0
                    m["source"] = "SYSTEM_SUGGESTION"
                    m["updated_at"] = datetime.utcnow().isoformat()
                    found = True
                    break
            if not found:
                modes.append({
                    "value": val,
                    "type": "disliked",
                    "source": "SYSTEM_SUGGESTION",
                    "strength": 1.0,
                    "confidence": 0.85,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
            pref.workplace_modes = modes

        elif key == "preferred_roles" and action == "add":
            roles = list(pref.preferred_roles)
            found = False
            for r in roles:
                if r.get("value") == val:
                    r["strength"] = 1.0
                    r["source"] = "SYSTEM_SUGGESTION"
                    r["updated_at"] = datetime.utcnow().isoformat()
                    found = True
                    break
            if not found:
                roles.append({
                    "value": val,
                    "source": "SYSTEM_SUGGESTION",
                    "strength": 1.0,
                    "confidence": 0.85,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
            pref.preferred_roles = roles

        sug.status = "ACCEPTED"
        sug.updated_at = datetime.utcnow()
        db.commit()
        return True

    @classmethod
    def dismiss_suggestion(cls, db: Session, suggestion_id: int) -> bool:
        sug = db.query(OptimizationSuggestion).filter(OptimizationSuggestion.id == suggestion_id).first()
        if not sug or sug.status != "PENDING":
            return False
        sug.status = "DISMISSED"
        sug.updated_at = datetime.utcnow()
        db.commit()
        return True

    @classmethod
    def remind_suggestion_later(cls, db: Session, suggestion_id: int) -> bool:
        sug = db.query(OptimizationSuggestion).filter(OptimizationSuggestion.id == suggestion_id).first()
        if not sug or sug.status != "PENDING":
            return False
        sug.status = "REMIND_LATER"
        sug.updated_at = datetime.utcnow()
        db.commit()
        return True
