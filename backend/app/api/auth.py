"""PatientTriage.ai — Auth API (Login)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import verify_password, create_access_token
from backend.app.models import Staff
from backend.app.schemas import LoginRequest, LoginResponse, StaffInfo

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate staff and return JWT token."""
    user = db.query(Staff).filter(Staff.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user.staff_id, "role": user.role})
    return LoginResponse(
        access_token = token,
        user         = StaffInfo(
            staff_id = user.staff_id,
            name     = user.name,
            email    = user.email,
            role     = user.role,
        )
    )
