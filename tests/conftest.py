import pytest
from app.database.connection import engine, Base
from app.models import (
    User,
    UserProfile,
    Education,
    Skill,
    Project,
    Certification,
    JobPreference,
    ApplicationPreference,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Ensures all database tables exist before running test suite.
    """
    Base.metadata.create_all(bind=engine)
    yield
