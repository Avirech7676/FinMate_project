from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import auth
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("", response_model=schemas.TransactionOut)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return TransactionService(db).create_transaction(current_user, transaction)

@router.get("", response_model=List[schemas.TransactionOut])
def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return TransactionService(db).list_transactions(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
        category=category,
        search=search
    )

@router.get("/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return TransactionService(db).get_transaction(transaction_id, current_user.user_id)

@router.put("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return TransactionService(db).update_transaction(transaction_id, current_user.user_id, transaction)

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return TransactionService(db).delete_transaction(transaction_id, current_user.user_id)
