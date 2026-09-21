ROLE_ADMIN = 0
ROLE_USER = 1

ROLE_LABELS = {
    ROLE_ADMIN: "admin",
    ROLE_USER: "user",
}


def is_admin(role: int) -> bool:
    return role == ROLE_ADMIN


def resolve_role_for_email(email: str, admin_emails: set[str]) -> int:
    if email.lower() in admin_emails:
        return ROLE_ADMIN
    return ROLE_USER
