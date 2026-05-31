from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.project_member import MemberRole
from app.repositories.project_member_repository import project_member_repo
from app.repositories.user_repository import user_repo
 
class MemberService:
 
    def check_is_member(self, db: Session, project_id: int, user_id: int):
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(
                status_code=403,
                detail="You must be a member of the project to perform this action"
            )
 
    def check_is_owner(self, db: Session, project_id: int, user_id: int):
        if not project_member_repo.is_owner(db, project_id, user_id):
            raise HTTPException(
                status_code=403,
                detail="Only project owner can perform this action"
            )
 
    def add_member(self, db: Session, project_id: int,
                   inviter_id: int, username: str, role: MemberRole):  # username thay vì user_id
        self.check_is_owner(db, project_id, inviter_id)
 
        # Tìm user theo username
        target_user = user_repo.get_by_username(db, username)
        if not target_user:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy username '{username}'")
 
        if project_member_repo.is_member(db, project_id, target_user.id):
            raise HTTPException(status_code=400, detail="User đã là thành viên của project này")
 
        return project_member_repo.add_member(db, project_id, target_user.id, role)
 
    def remove_member(self, db: Session, project_id: int,
                      remover_id: int, user_id: int):
        if remover_id != user_id:
            self.check_is_owner(db, project_id, remover_id)
 
        if project_member_repo.is_owner(db, project_id, user_id) and remover_id == user_id:
            raise HTTPException(
                status_code=400,
                detail="Owner cannot leave the project. Please delete the project or transfer ownership first."
            )
 
        success = project_member_repo.remove_member(db, project_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Member not found")
 
    def get_members(self, db: Session, project_id: int, requester_id: int):
        self.check_is_member(db, project_id, requester_id)
        return project_member_repo.get_project_members(db, project_id)
 
member_service = MemberService()