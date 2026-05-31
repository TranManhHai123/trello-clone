from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import project_service
from app.repositories.user_repository import user_repo

router = APIRouter(prefix="/projects", tags=["Projects"])


def _build_response(project, db: Session) -> ProjectResponse:
    owner = user_repo.get_by_id(db, project.owner_id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        owner_username=owner.username if owner else None,
    )


@router.get("", response_model=List[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = project_service.get_all(db, user_id=current_user.id)
    return [_build_response(p, db) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = project_service.create(
        db, name=data.name, owner_id=current_user.id, description=data.description
    )
    return _build_response(project, db)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = project_service.get_by_id(db, project_id=project_id, user_id=current_user.id)
    return _build_response(project, db)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = project_service.update(
        db, project_id=project_id, user_id=current_user.id,
        name=data.name, description=data.description
    )
    return _build_response(project, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service.delete(db, project_id=project_id, user_id=current_user.id)