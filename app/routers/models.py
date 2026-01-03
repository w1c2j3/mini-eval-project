from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import LLMModel
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=LLMModel)
def create_model(model: LLMModel, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model

@router.get("/", response_model=List[LLMModel])
def read_models(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    models = session.exec(select(LLMModel)).all()
    return models

