from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import EvaluationLog, EvaluationResult, TaskStatus
from app.core.evaluator import AsyncEvaluator
from app.core.security import get_current_user

router = APIRouter()

async def run_evaluation_task(task_id: int):
    evaluator = AsyncEvaluator(task_id)
    await evaluator.run()

@router.post("/", response_model=EvaluationLog)
async def create_task(
    model_id: int, 
    dataset_id: int, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    task = EvaluationLog(model_id=model_id, dataset_id=dataset_id, status=TaskStatus.PENDING)
    session.add(task)
    session.commit()
    session.refresh(task)
    
    background_tasks.add_task(run_evaluation_task, task.id)
    return task

@router.get("/", response_model=List[EvaluationLog])
def read_tasks(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    return session.exec(select(EvaluationLog).order_by(EvaluationLog.id.desc())).all()

@router.get("/{task_id}", response_model=EvaluationLog)
def read_task(task_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    task = session.get(EvaluationLog, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/{task_id}/results", response_model=List[EvaluationResult])
def read_task_results(
    task_id: int, 
    limit: int = 100, 
    offset: int = 0, 
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    results = session.exec(
        select(EvaluationResult)
        .where(EvaluationResult.task_id == task_id)
        .offset(offset)
        .limit(limit)
    ).all()
    return results

