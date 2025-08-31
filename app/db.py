from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os, json

DB_URL = os.getenv("DATABASE_URL", "sqlite:///state.db")
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class AllocationSnapshot(Base):
    __tablename__ = "allocation_snapshots"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data_json = Column(String)  # {strategy: allocation}

    @staticmethod
    def save(data: dict):
        with SessionLocal() as db:
            snap = AllocationSnapshot(id=str(datetime.utcnow().timestamp()),
                                      data_json=json.dumps(data))
            db.add(snap); db.commit()

Base.metadata.create_all(engine) 