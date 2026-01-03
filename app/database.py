from sqlmodel import SQLModel, Session, create_engine
from app.config import get_settings

settings = get_settings()

# Use pymysql for sync operations (like startup table creation)
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

