from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, index=True)
    email = mapped_column(String, unique=True, index=True, nullable=False)
    username = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password = mapped_column(String, nullable=False)
    is_active = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")

