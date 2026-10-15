"""
Database schema and utilities for QoS Buddy
Uses SQLite for simplicity
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///qos_buddy.db')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Alert(Base):
    """Store diagnostic alerts from Agent 2"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    issue_type = Column(String)
    severity = Column(String)
    kpis = Column(JSON)
    causes = Column(JSON)
    recommendations = Column(JSON)
    priority = Column(Integer)
    resolved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class KPIHistory(Base):
    """Store time-series KPI data"""
    __tablename__ = "kpi_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    cell_id = Column(String, index=True)
    rsrp = Column(Float)
    sinr = Column(Float)
    prb_ul = Column(Float)
    prb_dl = Column(Float)
    throughput_dl = Column(Float)
    throughput_ul = Column(Float)
    latency_ms = Column(Float)
    mos = Column(Float)
    handover_success_rate = Column(Float)


class ChatLog(Base):
    """Store chatbot conversation history"""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    user_message = Column(Text)
    assistant_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """Registered users for JWT authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")  # viewer | analyst | admin
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing QoS Buddy database...")
    init_db()
    print("Done!")
