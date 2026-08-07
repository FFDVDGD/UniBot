'''存储测试：独立数据边界、路径越界、原子写、State.toml 保护（验证点 15、16）。'''

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field

from Scripts.Extensions import (
    ExtensionConfigStore,
    ExtensionDataStore,
    StorageError,
    RESERVED_STATE_FILE,
)


class SampleConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    api_key: str = Field(default='', description='key')
    city: str = Field(default='Shanghai', min_length=1)


@pytest.fixture
def config_root(tmp_path: Path) -> Path:
    return tmp_path / 'Config' / 'Exs' / 'WeatherExt'


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    return tmp_path / 'Data' / 'Exs' / 'WeatherExt'


# ===== ExtensionConfigStore =====

class TestConfigStore:
    def test_save_and_load_roundtrip(self, config_root: Path):
        store = ExtensionConfigStore(config_root)
        model = SampleConfig(api_key='abc', city='Beijing')
        store.save(model)
        loaded = store.load(SampleConfig)
        assert loaded.api_key == 'abc'
        assert loaded.city == 'Beijing'

    def test_load_missing_uses_defaults(self, config_root: Path):
        store = ExtensionConfigStore(Path(config_root) / 'other')
        loaded = store.load(SampleConfig)
        assert loaded.api_key == ''
        assert loaded.city == 'Shanghai'

    def test_unknown_field_rejected_on_load(self, config_root: Path):
        store = ExtensionConfigStore(config_root)
        store.save(SampleConfig())
        # 手动写入未知字段
        config_file = config_root / 'Config.toml'
        config_file.write_text('api_key = "x"\nunknown = 1\n', encoding='Utf-8')
        with pytest.raises(Exception):
            store.load(SampleConfig)


# ===== ExtensionDataStore =====

class TestDataStore:
    def test_write_and_read_text(self, data_root: Path):
        store = ExtensionDataStore(data_root)
        store.write_text('notes.txt', 'hello')
        assert store.read_text('notes.txt') == 'hello'

    def test_write_and_read_json(self, data_root: Path):
        store = ExtensionDataStore(data_root)
        store.write_json('data.json', {'a': 1})
        assert store.read_json('data.json') == {'a': 1}

    def test_absolute_path_rejected(self, data_root: Path):
        store = ExtensionDataStore(data_root)
        with pytest.raises(StorageError):
            store.read_text('/etc/passwd')

    def test_parent_traversal_rejected(self, data_root: Path):
        store = ExtensionDataStore(data_root)
        with pytest.raises(StorageError):
            store.read_text('../secret.txt')

    def test_state_file_access_rejected(self, data_root: Path):
        store = ExtensionDataStore(data_root)
        with pytest.raises(StorageError):
            store.read_text(RESERVED_STATE_FILE)