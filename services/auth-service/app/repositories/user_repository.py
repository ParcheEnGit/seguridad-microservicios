from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_google_id(self, google_id: str) -> User | None:
        statement = select(User).where(User.google_id == google_id)
        return self.db.scalar(statement)

    def create(self, google_id: str, email: str, name: str) -> User:
        user = User(google_id=google_id, email=email, name=name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_or_create(self, google_id: str, email: str, name: str) -> User:
        existing = self.get_by_google_id(google_id)
        if existing:
            return existing
        return self.create(google_id=google_id, email=email, name=name)
