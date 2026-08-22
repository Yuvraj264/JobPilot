from fastapi.testclient import TestClient
from app.main import app
from app.models import User, UserProfile, Job, JobMatch, Application
from app.database.connection import SessionLocal

def test_demo_reset_flow():
    client = TestClient(app)
    
    # Trigger demo reset
    res = client.post("/api/demo/reset")
    assert res.status_code == 200
    assert res.json()["success"] is True
    
    # Query database to confirm demo records exist
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 99999).first()
        assert user is not None
        assert user.email == "demo.pilot@jobpilot.io"
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == 99999).first()
        assert profile is not None
        assert profile.full_name == "Alex Mercer"
        
        # Verify demo applications
        apps = db.query(Application).filter(Application.profile_id == profile.id).all()
        assert len(apps) == 2
        
        # Verify matches seeded
        matches = db.query(JobMatch).filter(JobMatch.profile_id == profile.id).all()
        assert len(matches) == 5
    finally:
        db.close()
