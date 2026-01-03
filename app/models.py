from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# --- Tables ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

class LLMModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    api_base_url: str
    api_key: str
    concurrency_limit: int = Field(default=5)
    model_name_identifier: str = Field(description="The model string to pass in API requests, e.g., 'gpt-3.5-turbo'")

    tasks: List["EvaluationLog"] = Relationship(back_populates="model")

class Dataset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    file_path: str
    total_count: int = Field(default=0)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    tasks: List["EvaluationLog"] = Relationship(back_populates="dataset")

class EvaluationLog(SQLModel, table=True):
    """Represents a single evaluation run (Task/Log)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="llmmodel.id")
    dataset_id: int = Field(foreign_key="dataset.id")
    
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    
    # Aggregate Stats (Updated after completion)
    accuracy: Optional[float] = Field(default=None, description="0.0 to 1.0")
    avg_latency_ms: Optional[float] = Field(default=None)
    avg_tokens: Optional[float] = Field(default=None)
    total_samples: int = Field(default=0)
    processed_samples: int = Field(default=0)

    model: Optional[LLMModel] = Relationship(back_populates="tasks")
    dataset: Optional[Dataset] = Relationship(back_populates="tasks")
    results: List["EvaluationResult"] = Relationship(back_populates="task")

class EvaluationResult(SQLModel, table=True):
    """Detailed result for each sample in a task"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="evaluationlog.id")
    
    question: str = Field(sa_column_kwargs={"type_": "TEXT"})
    ground_truth: str = Field(sa_column_kwargs={"type_": "TEXT"}) # From 'a' in JSONL
    
    # Model Output
    raw_output: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "TEXT"}) # From 'gen' or API response
    extracted_answer: Optional[str] = Field(default=None) # Parsed via Regex
    
    # Metrics
    is_correct: bool = Field(default=False)
    instruction_followed: bool = Field(default=False, description="Found 'answer:' pattern")
    latency_ms: float = Field(default=0.0)
    tokens_used: int = Field(default=0)
    
    task: Optional[EvaluationLog] = Relationship(back_populates="results")

