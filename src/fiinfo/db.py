from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fiinfo.config import get_settings
from fiinfo.models import Base

_state: dict = {"engine": None, "Session": None, "path": None}


def _ensure_engine():
    settings = get_settings()
    db_path = Path(settings.data_dir) / "fiinfo.db"
    if _state["engine"] is None or _state["path"] != db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}", future=True)
        _state.update(engine=engine, Session=sessionmaker(engine, expire_on_commit=False), path=db_path)
    return _state["engine"]


def init_db() -> None:
    Base.metadata.create_all(_ensure_engine())


def reset_engine() -> None:
    """Force re-read of settings (used by tests via monkeypatch)."""
    _state.update(engine=None, Session=None, path=None)


@contextmanager
def session_scope():
    _ensure_engine()
    s: Session = _state["Session"]()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
