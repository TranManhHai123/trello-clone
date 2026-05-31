from sqlalchemy.orm import Session
from app.models.project import Project
from typing import List, Optional

class ProjectRepository:
    def create(self, db: Session, name: str, owner_id: int,
           description: str | None = None) -> Project:
        project = Project(name=name, owner_id=owner_id, description=description)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    def get_by_id(self, db: Session, project_id: int) -> Project | None:
        return db.query(Project).filter(Project.id == project_id).first()

    def get_by_owner(self, db: Session, owner_id: int) -> List[Project]:
        return db.query(Project).filter(Project.owner_id == owner_id).all()

    def update(
        self,
        db: Session,
        project: Project,
        name: str | None = None,
        description: str | None = None,
    ) -> Project:
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        db.commit()
        db.refresh(project)
        return project
    
    def delete(self, db: Session, project: Project):
        db.delete(project)
        db.commit()

project_repo = ProjectRepository()