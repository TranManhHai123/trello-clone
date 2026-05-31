from fastapi import APIRouter
from app.api import auth, projects, tasks
from app.api import members 

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(members.router)  