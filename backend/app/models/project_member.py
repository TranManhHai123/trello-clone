from sqlalchemy import Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship, mapped_column
from app.core.database import Base
import enum

class MemberRole(str, enum.Enum):
    owner = "owner"
    member = "member"

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = mapped_column(Integer, primary_key=True, index=True)
    project_id = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = mapped_column(Enum(MemberRole), default=MemberRole.member, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")