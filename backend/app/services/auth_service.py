from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import user_repo
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    def register(self, db: Session, email: str, username: str, password: str):
        # Kiểm tra email đã tồn tại chưa
        if user_repo.get_by_email(db, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed = hash_password(password)
        return user_repo.create(
            db, email=email, username=username, hashed_password=hashed
        )

    def login(self, db: Session, email: str, password: str) -> str:
        user = user_repo.get_by_email(db, email)

        if not user or not verify_password(password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect",
            )

        return create_access_token({"sub": str(user.id)})


auth_service = AuthService()