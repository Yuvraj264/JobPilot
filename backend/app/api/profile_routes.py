from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.completeness_service import CompletenessService
from app.services.seed_service import seed_sample_profile
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileCompletenessResponse,
    ProfileSummaryResponse,
    EducationCreate,
    EducationUpdate,
    EducationResponse,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
    JobPreferenceUpdate,
    JobPreferenceResponse,
    ApplicationPreferenceUpdate,
    ApplicationPreferenceResponse,
)

router = APIRouter(prefix="/api/profile", tags=["User Profile"])


# --- Main Profile Endpoints ---
@router.get("", response_model=ProfileResponse)
def get_user_profile(db: Session = Depends(get_db)):
    """Retrieve full user profile details including education, skills, projects, certifications, and preferences."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found. Please create one.")
    return profile


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user_profile(data: ProfileCreate, db: Session = Depends(get_db)):
    """Create a new user profile or overwrite existing profile basic info."""
    return ProfileService.create_profile(db, data=data, user_id=1)


@router.put("", response_model=ProfileResponse)
def update_user_profile(data: ProfileUpdate, db: Session = Depends(get_db)):
    """Update basic and professional information for the user profile."""
    profile = ProfileService.update_profile(db, data=data, user_id=1)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
    return profile


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_profile(db: Session = Depends(get_db)):
    """Delete the user profile and all associated data."""
    deleted = ProfileService.delete_profile(db, user_id=1)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
    return None


@router.get("/summary", response_model=ProfileSummaryResponse)
def get_profile_summary(db: Session = Depends(get_db)):
    """Retrieve a compact structured summary of the user profile for AI matching engines."""
    profile = ProfileService.get_profile(db, user_id=1)
    return CompletenessService.generate_summary(profile)


@router.get("/completeness", response_model=ProfileCompletenessResponse)
def get_profile_completeness(db: Session = Depends(get_db)):
    """Calculate profile completeness percentage and identify missing sections."""
    profile = ProfileService.get_profile(db, user_id=1)
    return CompletenessService.calculate_completeness(profile)


# --- Education Endpoints ---
@router.get("/education", response_model=List[EducationResponse])
def get_educations(db: Session = Depends(get_db)):
    """List all education records for the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.get_educations(db, profile.id)


@router.post("/education", response_model=EducationResponse, status_code=201)
def add_education(data: EducationCreate, db: Session = Depends(get_db)):
    """Add an education record to the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create profile first.")
    return ProfileService.add_education(db, profile.id, data)


@router.put("/education/{id}", response_model=EducationResponse)
def update_education(id: int, data: EducationUpdate, db: Session = Depends(get_db)):
    """Update an existing education record."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    edu = ProfileService.update_education(db, edu_id=id, profile_id=profile.id, data=data)
    if not edu:
        raise HTTPException(status_code=404, detail="Education record not found.")
    return edu


@router.delete("/education/{id}", status_code=204)
def delete_education(id: int, db: Session = Depends(get_db)):
    """Delete an education record."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    deleted = ProfileService.delete_education(db, edu_id=id, profile_id=profile.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Education record not found.")
    return None


# --- Skill Endpoints ---
@router.get("/skills", response_model=List[SkillResponse])
def get_skills(db: Session = Depends(get_db)):
    """List all skills for the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.get_skills(db, profile.id)


@router.post("/skills", response_model=SkillResponse, status_code=201)
def add_skill(data: SkillCreate, db: Session = Depends(get_db)):
    """Add a new skill to the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create profile first.")
    return ProfileService.add_skill(db, profile.id, data)


@router.put("/skills/{id}", response_model=SkillResponse)
def update_skill(id: int, data: SkillUpdate, db: Session = Depends(get_db)):
    """Update an existing skill entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    skill = ProfileService.update_skill(db, skill_id=id, profile_id=profile.id, data=data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill record not found.")
    return skill


@router.delete("/skills/{id}", status_code=204)
def delete_skill(id: int, db: Session = Depends(get_db)):
    """Delete a skill entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    deleted = ProfileService.delete_skill(db, skill_id=id, profile_id=profile.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill record not found.")
    return None


# --- Project Endpoints ---
@router.get("/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    """List all projects for the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.get_projects(db, profile.id)


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def add_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Add a new project to the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create profile first.")
    return ProfileService.add_project(db, profile.id, data)


@router.put("/projects/{id}", response_model=ProjectResponse)
def update_project(id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    proj = ProfileService.update_project(db, project_id=id, profile_id=profile.id, data=data)
    if not proj:
        raise HTTPException(status_code=404, detail="Project record not found.")
    return proj


@router.delete("/projects/{id}", status_code=204)
def delete_project(id: int, db: Session = Depends(get_db)):
    """Delete a project entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    deleted = ProfileService.delete_project(db, project_id=id, profile_id=profile.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project record not found.")
    return None


# --- Certification Endpoints ---
@router.get("/certifications", response_model=List[CertificationResponse])
def get_certifications(db: Session = Depends(get_db)):
    """List all certifications for the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.get_certifications(db, profile.id)


@router.post("/certifications", response_model=CertificationResponse, status_code=201)
def add_certification(data: CertificationCreate, db: Session = Depends(get_db)):
    """Add a new certification to the user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create profile first.")
    return ProfileService.add_certification(db, profile.id, data)


@router.put("/certifications/{id}", response_model=CertificationResponse)
def update_certification(id: int, data: CertificationUpdate, db: Session = Depends(get_db)):
    """Update an existing certification entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    cert = ProfileService.update_certification(db, cert_id=id, profile_id=profile.id, data=data)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found.")
    return cert


@router.delete("/certifications/{id}", status_code=204)
def delete_certification(id: int, db: Session = Depends(get_db)):
    """Delete a certification entry."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    deleted = ProfileService.delete_certification(db, cert_id=id, profile_id=profile.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Certification record not found.")
    return None


# --- Preferences Endpoints ---
@router.get("/preferences")
def get_preferences(db: Session = Depends(get_db)):
    """Retrieve job preferences and application preferences."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return {
        "job_preference": profile.job_preference,
        "application_preference": profile.application_preference,
    }


@router.put("/preferences/job", response_model=JobPreferenceResponse)
def update_job_preferences(data: JobPreferenceUpdate, db: Session = Depends(get_db)):
    """Update target roles, preferred locations, salary expectations, and job preferences."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.update_job_preferences(db, profile_id=profile.id, data=data)


@router.put("/preferences/application", response_model=ApplicationPreferenceResponse)
def update_application_preferences(data: ApplicationPreferenceUpdate, db: Session = Depends(get_db)):
    """Update application automation behavior preferences."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return ProfileService.update_application_preferences(db, profile_id=profile.id, data=data)


# --- Dev Sample Seed Endpoint ---
@router.post("/seed", response_model=ProfileResponse, status_code=201)
def seed_dev_profile(db: Session = Depends(get_db)):
    """Development-only helper to seed a full realistic sample profile for quick testing."""
    return seed_sample_profile(db, user_id=1)
