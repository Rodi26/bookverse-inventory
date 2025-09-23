

import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):

    database_url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    model_config = ConfigDict(env_prefix="DB_")


_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def create_database_engine(config: DatabaseConfig) -> Engine:

    global _engine

    if _engine is None:
        _engine = create_engine(
            config.database_url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info(f"✅ Database engine created: {config.database_url}")

    return _engine


def create_session_factory(engine: Engine) -> sessionmaker:

    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
        )
        logger.info("✅ Database session factory created")

    return _session_factory


def get_database_session(
        config: DatabaseConfig) -> Generator[Session, None, None]:

    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)

    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Database session error: {e}")
        raise
    finally:
        session.close()


@contextmanager
def database_session_context(
        config: DatabaseConfig) -> Generator[Session, None, None]:

    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Database context error: {e}")
        raise
    finally:
        session.close()


def create_tables(config: DatabaseConfig, base_class):

    try:
        engine = create_database_engine(config)
        base_class.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def test_database_connection(config: DatabaseConfig) -> bool:

    try:
        engine = create_database_engine(config)
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("✅ Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


def reset_database_globals():

    global _engine, _session_factory

    if _engine:
        _engine.dispose()
        _engine = None

    _session_factory = None
    logger.info("🔄 Database globals reset")
