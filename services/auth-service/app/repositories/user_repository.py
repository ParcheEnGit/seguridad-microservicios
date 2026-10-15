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

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.scalar(statement)

    def create(
        self,
        google_id: str | None,
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

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.role, User.name, User.email)))

    def invite(self, *, name: str, email: str, role: int) -> User:
        return self.create(
            google_id=None,
            email=email.strip().lower(),
            name=name.strip(),
            role=role,
        )

    def link_google_identity(self, user: User, *, google_id: str, picture_url: str | None) -> User:
        user.google_id = google_id
        user.picture_url = picture_url
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

    def _sync_profile(self, user: User, *, name: str, picture_url: str | None) -> User:
        # El nombre es administrado por quien autorizó la cuenta; Google solo
        # actualiza la fotografía al iniciar sesión.
        if user.picture_url != picture_url:
            return self.update_profile(
                user,
                name=user.name,
                role=user.role,
                picture_url=picture_url,
            )
        return user

    def get_or_create(
        self,
        google_id: str,
        email: str,
        name: str,
        picture_url: str | None,
        admin_emails: set[str],
    ) -> User:
        del admin_emails  # La autorización es explícita desde la administración de usuarios.
        existing = self.get_by_google_id(google_id)
        if existing:
            return self._sync_profile(existing, name=name, picture_url=picture_url)

        # Un correo autorizado puede existir antes de su primer acceso con Google.
        invited = self.get_by_email(email)
        if invited:
            return self.link_google_identity(
                invited,
                google_id=google_id,
                picture_url=picture_url,
            )

        raise PermissionError("El correo no está autorizado por un administrador de LabSentinel")
