from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_owner_sku_index() -> None:
    """Apply a small compatibility migration for databases created before SKU uniqueness."""
    with engine.begin() as connection:
        duplicates = connection.execute(text(
            "SELECT owner_id, sku, COUNT(*) AS count FROM products "
            "GROUP BY owner_id, sku HAVING COUNT(*) > 1 LIMIT 1"
        )).first()
        if duplicates:
            raise RuntimeError(
                "Duplicate owner/SKU records exist. Resolve them before starting the API; "
                "the inventory integrity index cannot be created."
            )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_products_owner_sku ON products(owner_id, sku)"
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
