from sqlalchemy import Integer, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column
from app.core.database import Base
import enum

class RequestAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"

class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class TaskRequest(Base):
    __tablename__ = "task_requests"

    id = mapped_column(Integer, primary_key=True, index=True)
    project_id = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)  
    requester_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = mapped_column(Enum(RequestAction), nullable=False)
    payload = mapped_column(JSON, nullable=True)  # dữ liệu cần khi approve (title, status mới...)
    status = mapped_column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())