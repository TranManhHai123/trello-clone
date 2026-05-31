from pydantic import BaseModel
from app.models.project_member import MemberRole

class MemberAdd(BaseModel):
    username: str
    role: MemberRole = MemberRole.member

class MemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: MemberRole
    user_email: str | None = None
    user_username: str | None = None 
    
    model_config = {"from_attributes": True}