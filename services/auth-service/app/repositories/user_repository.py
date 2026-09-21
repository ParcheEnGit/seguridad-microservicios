from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import resolve_role_for_email
from app.db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_google_id(self, google_id: str) -> User | None:
        statement = select(User).where(User.google_id == google_id)
        return self.db.scalar(statement)

    def create(
        self,
        google_id: str,
        email: str,
        name: str,
        role: int,
        picture_url: str | None = None,
    ) -> User:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            role=role,
            picture_url=picture_url,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(
        self,
        user: User,
        *,
        name: str,
        role: int,
        picture_url: str | None,
    ) -> User:
        user.name = name
        user.role = role
        user.picture_url = picture_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_or_create(
        self,
        google_id: str,
        email: str,
        name: str,
        picture_url: str | None,
        admin_emails: set[str],
    ) -> User:
        role = resolve_role_for_email(email, admin_emails)
        existing = self.get_by_google_id(google_id)
        if existing:
            if (
                existing.role != role
                or existing.name != name
                or existing.picture_url != picture_url
            ):
                return self.update_profile(
                    existing,
                    name=name,
                    role=role,
                    picture_url=picture_url,
                )
            return existing
        return self.create(
            google_id=google_id,
            email=email,
            name=name,
            role=role,
            picture_url=picture_url,
        )
