"""Database connection management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from contextlib import contextmanager

from db.models import Base


def get_db_path() -> Path:
    """Get database file path.

    Returns:
        Path to ~/.config/vpn/vpn.db
    """
    config_dir = Path.home() / '.config' / 'vpn'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'vpn.db'


# Global engine and session factory
_db_path = get_db_path()
engine = create_engine(f'sqlite:///{_db_path}', echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables.

    Creates all tables defined in models.py if they don't exist.
    """
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    """Get database session with automatic cleanup.

    Usage:
        with get_db() as db:
            db.query(CloudCredential).all()

    Yields:
        SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
