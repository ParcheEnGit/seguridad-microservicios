from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def apply_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "role" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN role INTEGER NOT NULL DEFAULT 1"
                )
            )
        if "picture_url" not in columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN picture_url VARCHAR(2048)")
            )
        if "google_id" in columns:
            connection.execute(text("ALTER TABLE users ALTER COLUMN google_id DROP NOT NULL"))
        if "keycloak_id" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN keycloak_id VARCHAR(255)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_keycloak_id ON users(keycloak_id)"))
