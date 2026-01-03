import shutil
import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Dataset
from app.config import get_settings
from app.core.security import get_current_user

router = APIRouter()
settings = get_settings()

@router.post("/upload", response_model=Dataset)
async def upload_dataset(
    name: str, 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    file_location = f"{settings.UPLOAD_DIR}/{file.filename}"
    
    # Save file
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Count lines (simple implementation)
    count = 0
    with open(file_location, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
            
    dataset = Dataset(name=name, file_path=file_location, total_count=count)
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset

@router.get("/", response_model=List[Dataset])
def read_datasets(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    return session.exec(select(Dataset)).all()

