"""Inventory routes for manual import and current valuation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_inventory_service
from app.database import get_db
from app.schemas.inventory import InventoryImportRequest, InventoryImportResponse, InventoryResponse
from app.security.deps import require_active_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/me", response_model=InventoryResponse)
def inventory_me(
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    inventory_service=Depends(get_inventory_service),
):
    return inventory_service.get_inventory(db, current_user)


@router.post("/import", response_model=InventoryImportResponse)
def import_inventory(
    payload: InventoryImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    inventory_service=Depends(get_inventory_service),
):
    result = inventory_service.import_inventory(
        db,
        current_user,
        items=payload.items,
        replace_existing=payload.replace_existing,
    )
    db.commit()
    return InventoryImportResponse(**result)
