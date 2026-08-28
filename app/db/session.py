"""数据库引擎与 Session。

- 同步驱动（PyMySQL），不要 async
- 通过 FastAPI 依赖 get_session 拿 session，yield 后自动 close
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖：每请求一个 session，用完关闭。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
