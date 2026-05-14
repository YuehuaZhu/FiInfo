import pytest

from fiinfo import config as _config
from fiinfo import db as _db


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """每个测试用临时 data_dir,并重置 engine 缓存。"""
    monkeypatch.setenv("FIINFO_DATA_DIR", str(tmp_path))
    # 重新加载 settings 单例
    _config.settings = _config.get_settings()
    _db.reset_engine()
    yield tmp_path
    _db.reset_engine()
