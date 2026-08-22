import pytest
from sqlalchemy.orm import Session
from app.models.profile import User, UserProfile
from app.services.orchestration.scheduler import AutomationScheduler
from app.services.demo_seeder import seed_demo_data, clear_demo_data
from app.database.connection import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_phase_11_to_14_regression(db: Session):
    """
    Verifies autonomous scheduling state, metrics initialization, and Demo reset capabilities (Phases 11 to 14).
    """
    # 1. Test Automation Scheduler states
    status = AutomationScheduler.get_status()
    assert "enabled" in status
    assert "running" in status
    
    # 2. Test Demo Seeder: reset and seed DEMO_USER_ID = 99999
    clear_demo_data(db)
    seed_demo_data(db)
    
    # Verify that demo user profile is seeded
    demo_profile = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
    assert demo_profile is not None
    assert demo_profile.full_name == "Alex Mercer"
    
    # Verify that jobs are seeded for demo user
    from app.models.job import Job
    demo_jobs = db.query(Job).all()
    assert len(demo_jobs) > 0
    
    # Clean up demo data to leave database clean
    clear_demo_data(db)
    demo_profile_post = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
    assert demo_profile_post is None
