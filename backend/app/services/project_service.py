from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List

from app.repositories.project_repository import project_repo
from app.repositories.project_member_repository import project_member_repo
from app.models.project import Project
from app.models.project_member import MemberRole


class ProjectService:

    def create(self, db: Session, name: str, owner_id: int,
               description: Optional[str] = None) -> Project:
        project = project_repo.create(db, name=name, owner_id=owner_id, description=description)
        project_member_repo.add_member(db, project_id=project.id,
                                       user_id=owner_id, role=MemberRole.owner)
        return project

    def get_all(self, db: Session, user_id: int) -> List[Project]:
        memberships = project_member_repo.get_memberships_by_user(db, user_id)
        project_ids = [m.project_id for m in memberships]
        return db.query(Project).filter(Project.id.in_(project_ids)).all()

    def get_by_id(self, db: Session, project_id: int, user_id: int) -> Project:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to access this project")

        project = project_repo.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project does not exist")
        return project

    def update(self, db: Session, project_id: int, user_id: int,
               name: Optional[str] = None, description: Optional[str] = None) -> Project:
        if not project_member_repo.is_owner(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="Only owner can update the project")

        project = project_repo.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project does not exist")

        return project_repo.update(db, project, name=name, description=description)

    def delete(self, db: Session, project_id: int, user_id: int) -> None:
        if not project_member_repo.is_owner(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="Only owner can delete the project")

        project = project_repo.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project does not exist")

        project_repo.delete(db, project)


project_service = ProjectService()