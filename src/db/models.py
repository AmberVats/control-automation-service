import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class ControlModel(Base):
    __tablename__ = "controls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1")
    component = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(100), nullable=True, default="product_control_analytics")
    schedule = Column(String(50), nullable=True)
    config_yaml = Column(Text, nullable=False)
    config_hash = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ControlRunModel(Base):
    __tablename__ = "control_runs"

    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    control_name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    config_hash = Column(String(64), nullable=False, index=True)
    triggered_by = Column(String(50), default="api", nullable=False)
    as_of_date = Column(String(20), nullable=True)
    start_time = Column(DateTime, default=utc_now, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # PASS, BREACH, FAIL
    row_count_in = Column(Integer, default=0)
    row_count_out = Column(Integer, default=0)
    breach_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    exceptions = relationship(
        "ControlExceptionModel",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ControlExceptionModel.id"
    )


class ControlExceptionModel(Base):
    __tablename__ = "control_exceptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("control_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    exception_type = Column(String(50), nullable=False)
    key_data = Column(Text, nullable=True)
    field = Column(String(100), nullable=True)
    source_val = Column(Text, nullable=True)
    target_val = Column(Text, nullable=True)
    difference = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("ControlRunModel", back_populates="exceptions")


# Indexes for analytics and performance
Index("idx_runs_ctrl_status", ControlRunModel.control_name, ControlRunModel.status)
Index("idx_runs_created", ControlRunModel.created_at)
