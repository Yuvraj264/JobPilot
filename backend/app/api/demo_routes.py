from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.demo_seeder import seed_demo_data, clear_demo_data

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_demo_mode(db: Session = Depends(get_db)):
    """
    Clears all existing synthetic demo data and re-seeds it.
    Uses dedicated User ID 99999 to prevent contamination of production/real user profiles.
    """
    seed_demo_data(db)
    return {"success": True, "message": "Demo environment reset completed successfully."}
