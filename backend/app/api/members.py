from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.project_member import MemberAdd, MemberResponse
from app.services.member_service import member_service
from app.repositories.user_repository import user_repo

router = APIRouter(prefix="/projects/{project_id}/members", tags=["Members"])


def _build_response(member, user) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        user_email=user.email if user else None,
        user_username=user.username if user else None,
    )


@router.get("", response_model=List[MemberResponse])
def list_members(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    members = member_service.get_members(db, project_id, current_user.id)
    return [_build_response(m, user_repo.get_by_id(db, m.user_id)) for m in members]


@router.post("", response_model=MemberResponse, status_code=201)
def add_member(project_id: int, data: MemberAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = member_service.add_member(db, project_id=project_id, inviter_id=current_user.id,
                                       username=data.username, role=data.role)
    return _build_response(member, user_repo.get_by_id(db, member.user_id))


@router.delete("/{user_id}", status_code=204)
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member_service.remove_member(db, project_id=project_id, remover_id=current_user.id, user_id=user_id)