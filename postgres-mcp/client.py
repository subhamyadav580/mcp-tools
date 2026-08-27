import logging
import os
from threading import Lock
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(Database, cls).__new__(cls)
                    instance.engine = None
                    instance.SessionLocal = None
                    instance._init_lock = Lock()
                    cls._instance = instance
        return cls._instance

    def _ensure_connected(self) -> None:
        if self.engine is not None:
            return
        with self._init_lock:
            if self.engine is not None:
                return
            logger.info("Connecting to database: %s", DATABASE_URL)
            self.engine = create_engine(
                DATABASE_URL,
                echo=False,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 60,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                },
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            logger.info("Database engine initialized successfully")

    def get_session(self) -> Session:
        self._ensure_connected()
        return self.SessionLocal()

    def get_db(self) -> Generator[Session, None, None]:
        """Dependency injection for FastAPI routes."""
        db = self.get_session()
        try:
            yield db
        finally:
            db.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")


# Singleton placeholder — no connection opened until first use
db_instance = Database()
