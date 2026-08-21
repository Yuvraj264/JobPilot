from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.profile import (
    User,
    UserProfile,
    Education,
    Skill,
    Project,
    Certification,
    JobPreference,
    ApplicationPreference,
)
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    EducationCreate,
    EducationUpdate,
    SkillCreate,
    SkillUpdate,
    ProjectCreate,
    ProjectUpdate,
    CertificationCreate,
    CertificationUpdate,
    JobPreferenceUpdate,
    ApplicationPreferenceUpdate,
)


class ProfileService:
    """
    Service encapsulating database CRUD operations for User Profile and related sub-entities.
    Initial phase assumes a single default user (user_id = 1).
    """

    @staticmethod
    def get_or_create_user(db: Session, email: str = "default.user@jobpilot.local") -> User:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_profile(db: Session, user_id: int = 1) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    @staticmethod
    def create_profile(db: Session, data: ProfileCreate, user_id: int = 1) -> UserProfile:
        ProfileService.get_or_create_user(db, email=data.email)
        
        # Check if profile already exists
        existing = ProfileService.get_profile(db, user_id=user_id)
        if existing:
            # Update existing
            for key, val in data.model_dump().items():
                setattr(existing, key, val)
            db.commit()
            db.refresh(existing)
            return existing

        profile = UserProfile(user_id=user_id, **data.model_dump())
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Initialize default job and application preferences
        job_pref = JobPreference(profile_id=profile.id)
        app_pref = ApplicationPreference(profile_id=profile.id)
        db.add_all([job_pref, app_pref])
        db.commit()
        db.refresh(profile)

        return profile

    @staticmethod
    def update_profile(db: Session, data: ProfileUpdate, user_id: int = 1) -> Optional[UserProfile]:
        profile = ProfileService.get_profile(db, user_id=user_id)
        if not profile:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(profile, key, val)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete_profile(db: Session, user_id: int = 1) -> bool:
        profile = ProfileService.get_profile(db, user_id=user_id)
        if not profile:
            return False
        db.delete(profile)
        db.commit()
        return True

    # --- Education CRUD ---
    @staticmethod
    def get_educations(db: Session, profile_id: int) -> List[Education]:
        return db.query(Education).filter(Education.profile_id == profile_id).all()

    @staticmethod
    def add_education(db: Session, profile_id: int, data: EducationCreate) -> Education:
        edu = Education(profile_id=profile_id, **data.model_dump())
        db.add(edu)
        db.commit()
        db.refresh(edu)
        return edu

    @staticmethod
    def update_education(db: Session, edu_id: int, profile_id: int, data: EducationUpdate) -> Optional[Education]:
        edu = db.query(Education).filter(Education.id == edu_id, Education.profile_id == profile_id).first()
        if not edu:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(edu, key, val)
        db.commit()
        db.refresh(edu)
        return edu

    @staticmethod
    def delete_education(db: Session, edu_id: int, profile_id: int) -> bool:
        edu = db.query(Education).filter(Education.id == edu_id, Education.profile_id == profile_id).first()
        if not edu:
            return False
        db.delete(edu)
        db.commit()
        return True

    # --- Skill CRUD ---
    @staticmethod
    def get_skills(db: Session, profile_id: int) -> List[Skill]:
        return db.query(Skill).filter(Skill.profile_id == profile_id).all()

    @staticmethod
    def add_skill(db: Session, profile_id: int, data: SkillCreate) -> Skill:
        skill = Skill(profile_id=profile_id, **data.model_dump())
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def update_skill(db: Session, skill_id: int, profile_id: int, data: SkillUpdate) -> Optional[Skill]:
        skill = db.query(Skill).filter(Skill.id == skill_id, Skill.profile_id == profile_id).first()
        if not skill:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(skill, key, val)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete_skill(db: Session, skill_id: int, profile_id: int) -> bool:
        skill = db.query(Skill).filter(Skill.id == skill_id, Skill.profile_id == profile_id).first()
        if not skill:
            return False
        db.delete(skill)
        db.commit()
        return True

    # --- Project CRUD ---
    @staticmethod
    def get_projects(db: Session, profile_id: int) -> List[Project]:
        return db.query(Project).filter(Project.profile_id == profile_id).all()

    @staticmethod
    def add_project(db: Session, profile_id: int, data: ProjectCreate) -> Project:
        proj = Project(profile_id=profile_id, **data.model_dump())
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    @staticmethod
    def update_project(db: Session, project_id: int, profile_id: int, data: ProjectUpdate) -> Optional[Project]:
        proj = db.query(Project).filter(Project.id == project_id, Project.profile_id == profile_id).first()
        if not proj:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(proj, key, val)
        db.commit()
        db.refresh(proj)
        return proj

    @staticmethod
    def delete_project(db: Session, project_id: int, profile_id: int) -> bool:
        proj = db.query(Project).filter(Project.id == project_id, Project.profile_id == profile_id).first()
        if not proj:
            return False
        db.delete(proj)
        db.commit()
        return True

    # --- Certification CRUD ---
    @staticmethod
    def get_certifications(db: Session, profile_id: int) -> List[Certification]:
        return db.query(Certification).filter(Certification.profile_id == profile_id).all()

    @staticmethod
    def add_certification(db: Session, profile_id: int, data: CertificationCreate) -> Certification:
        cert = Certification(profile_id=profile_id, **data.model_dump())
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def update_certification(db: Session, cert_id: int, profile_id: int, data: CertificationUpdate) -> Optional[Certification]:
        cert = db.query(Certification).filter(Certification.id == cert_id, Certification.profile_id == profile_id).first()
        if not cert:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(cert, key, val)
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def delete_certification(db: Session, cert_id: int, profile_id: int) -> bool:
        cert = db.query(Certification).filter(Certification.id == cert_id, Certification.profile_id == profile_id).first()
        if not cert:
            return False
        db.delete(cert)
        db.commit()
        return True

    # --- Preferences CRUD ---
    @staticmethod
    def update_job_preferences(db: Session, profile_id: int, data: JobPreferenceUpdate) -> JobPreference:
        pref = db.query(JobPreference).filter(JobPreference.profile_id == profile_id).first()
        if not pref:
            pref = JobPreference(profile_id=profile_id, **data.model_dump())
            db.add(pref)
        else:
            for key, val in data.model_dump().items():
                setattr(pref, key, val)
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def update_application_preferences(db: Session, profile_id: int, data: ApplicationPreferenceUpdate) -> ApplicationPreference:
        pref = db.query(ApplicationPreference).filter(ApplicationPreference.profile_id == profile_id).first()
        if not pref:
            pref = ApplicationPreference(profile_id=profile_id, **data.model_dump())
            db.add(pref)
        else:
            for key, val in data.model_dump().items():
                setattr(pref, key, val)
        db.commit()
        db.refresh(pref)
        return pref
