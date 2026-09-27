from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from utils.logger import get_logger


logger = get_logger(__name__)


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_engine():
    return engine


@contextmanager
def get_db_connection():
    connection = engine.connect()

    try:
        yield connection

    finally:
        connection.close()


@contextmanager
def get_db_session():
    session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()