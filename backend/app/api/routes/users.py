"""User profile routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdateRequest
from app.security.deps import get_user_service, require_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def users_me(current_user=Depends(require_active_user)):
    return UserResponse.from_model(current_user)


@router.patch("/me", response_model=UserResponse)
def update_users_me(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    user_service=Depends(get_user_service),
):
    updates = payload.model_dump(exclude_unset=True)
    user = user_service.update_profile(db, current_user, updates)
    db.commit()
    db.refresh(user)
    return UserResponse.from_model(user)
