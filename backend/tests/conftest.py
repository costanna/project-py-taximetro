import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import os  # noqa: E402

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ALLOWED_ORIGINS", "*")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import database  # noqa: E402
import main  # noqa: E402


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    ruta_bd = tmp_path / "test.db"
    engine_test = create_engine(
        f"sqlite:///{ruta_bd}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    database.Base.metadata.create_all(bind=engine_test)

    def _get_db_test():
        db = SessionLocalTest()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setenv("SECRET_KEY", "clave-de-test")
    main.app.dependency_overrides[main.get_db] = _get_db_test
    with TestClient(main.app) as cliente_test:
        yield cliente_test
    main.app.dependency_overrides.clear()
