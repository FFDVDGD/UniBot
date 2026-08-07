'''扩展独立配置与数据存储工具。

每个扩展使用作用域受限的 `Config/Exs/<id>/Config.toml` 与 `Data/Exs/<id>/`，
拒绝绝对路径、`..` 越界、访问其它扩展目录及覆盖框架保留文件。
所有写操作默认原子提交，失败时保留旧文件。
'''

import json
import tempfile
from pathlib import Path
from typing import Any

from nonebot.log import logger
from pydantic import BaseModel

from Scripts.Extensions.Base import StorageError

# 框架保留文件，扩展不得写入
RESERVED_STATE_FILE = 'State.toml'
# 各扩展配置文件名
CONFIG_FILE_NAME = 'Config.toml'


def _check_relative(relative: str) -> Path:
    '''校验相对路径不越界、为绝对路径时拒绝，并返回规范化后的 Path。'''
    path = Path(relative)
    if path.is_absolute():
        raise StorageError(f'不允许使用绝对路径：{relative}')
    normalized = Path(*path.parts)
    if '..' in path.parts or '..' in str(normalized):
        raise StorageError(f'不允许路径越界：{relative}')
    return normalized


def _atomic_write_text(file_path: Path, content: str) -> None:
    '''使用临时文件与原子替换写入文本，失败时保留旧文件。'''
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            'w', encoding='Utf-8', dir=file_path.parent, suffix='.tmp', delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(file_path)
    except Exception as error:
        logger.error(f'写入文件失败：{file_path}！错误：{error}')
        raise StorageError(f'写入文件失败：{error}') from error


def _atomic_write_bytes(file_path: Path, content: bytes) -> None:
    '''使用临时文件与原子替换写入字节，失败时保留旧文件。'''
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            'wb', dir=file_path.parent, suffix='.tmp', delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(file_path)
    except Exception as error:
        logger.error(f'写入文件失败：{file_path}！错误：{error}')
        raise StorageError(f'写入文件失败：{error}') from error


class ExtensionConfigStore:
    '''当前扩展独占的 Config.toml 读写工具。'''

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.config_path = root_dir / CONFIG_FILE_NAME

    def load(self, model: type[BaseModel]) -> BaseModel:
        '''从当前扩展的 Config.toml 读取并执行 model_validate，文件缺失时用默认值。'''
        if not self.config_path.exists():
            return model()
        try:
            import tomllib
            data = tomllib.loads(self.config_path.read_text('Utf-8'))
            return model.model_validate(data)
        except Exception as error:
            raise StorageError(f'扩展配置加载失败：{error}') from error

    def save(self, model: BaseModel) -> None:
        '''使用 model_dump(mode='json') 整体原子替换 Config.toml。'''
        import tomlkit
        content = tomlkit.dumps(model.model_dump(mode='json'))
        _atomic_write_text(self.config_path, content)


class ExtensionDataStore:
    '''当前扩展独占的 Data/ 读写工具，所有路径经越界与保留文件检查。'''

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def _resolve(self, relative: str) -> Path:
        '''将相对路径解析为根目录内的安全绝对路径。'''
        normalized = _check_relative(relative)
        if normalized.name == RESERVED_STATE_FILE or RESERVED_STATE_FILE in normalized.parts:
            raise StorageError(f'不允许访问框架保留文件：{RESERVED_STATE_FILE}')
        return self.root_dir / normalized

    def path(self, relative: str) -> Path:
        '''返回根目录内安全解析后的路径（不保证存在）。'''
        return self._resolve(relative)

    def read_text(self, relative: str) -> str:
        '''读取文本文件。'''
        return self._resolve(relative).read_text('Utf-8')

    def write_text(self, relative: str, content: str) -> None:
        '''原子写入文本文件。'''
        _atomic_write_text(self._resolve(relative), content)

    def read_json(self, relative: str) -> Any:
        '''读取 JSON 文件并解析。'''
        return json.loads(self._resolve(relative).read_text('Utf-8'))

    def write_json(self, relative: str, data: Any) -> None:
        '''原子写入 JSON 文件。'''
        content = json.dumps(data, ensure_ascii=False, indent=2)
        _atomic_write_text(self._resolve(relative), content)

    def read_bytes(self, relative: str) -> bytes:
        '''读取字节文件。'''
        return self._resolve(relative).read_bytes()

    def write_bytes(self, relative: str, content: bytes) -> None:
        '''原子写入字节文件。'''
        _atomic_write_bytes(self._resolve(relative), content)