from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class Task(Base):
    __tablename__ = "tasks"

    id = mapped_column(Integer, primary_key=True, index=True)
    title = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=True)
    status = mapped_column(Enum(TaskStatus), default=TaskStatus.todo)
    project_id = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_to = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="tasks")