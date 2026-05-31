from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.project_member import ProjectMember, MemberRole
from app.models.user import User

class ProjectMemberRepository:

    def add_member(self, db: Session, project_id: int, user_id: int,
                   role: MemberRole = MemberRole.member) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def get_member(self, db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
    
    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_project_members(self, db: Session, project_id: int) -> List[ProjectMember]:
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()
    
    def get_memberships_by_user(self, db: Session, user_id: int) -> List[ProjectMember]:
        """Lấy tất cả membership của một user (dùng để lấy danh sách project)"""
        return db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()

    def remove_member(self, db: Session, project_id: int, user_id: int) -> bool:
        member = self.get_member(db, project_id, user_id)
        if not member:
            return False
        db.delete(member)
        db.commit()
        return True

    def is_member(self, db: Session, project_id: int, user_id: int) -> bool:
        return self.get_member(db, project_id, user_id) is not None

    def is_owner(self, db: Session, project_id: int, user_id: int) -> bool:
        member = self.get_member(db, project_id, user_id)
        return member is not None and member.role == MemberRole.owner

project_member_repo = ProjectMemberRepository()