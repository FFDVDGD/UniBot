'''扩展 Python 依赖聚合：扫描扩展清单，同步到 pyproject.toml 的 extensions 组。

扩展通过 `Extension.toml` 的 `[dependencies].python` 声明第三方 Python 库。
本模块把所有扩展的依赖聚合去重后写入 `pyproject.toml` 的
`[project.optional-dependencies].extensions` 组，供 `uv sync --extra extensions`
统一安装。卸载扩展后再次聚合，避免残留无用依赖。
'''

import tomllib
from pathlib import Path

import tomlkit

# 扩展目录根与清单文件名（与 Loader 保持一致）
EXTENSIONS_DIR = Path('Extensions')
MANIFEST_FILE = 'Extension.toml'
PYPROJECT_PATH = Path('pyproject.toml')
# 收集所有扩展依赖的 optional-dependencies 组名
EXTENSIONS_EXTRA = 'extensions'


def _read_extension_dependencies(manifest_path: Path) -> list[str]:
    '''读取单个扩展清单中的 [dependencies].python 依赖列表。'''
    try:
        data = tomllib.loads(manifest_path.read_text('Utf-8'))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    dependencies = data.get('dependencies', {})
    python = dependencies.get('python', [])
    return list(python) if isinstance(python, list) else []


def collect_extension_dependencies() -> list[str]:
    '''扫描 Extensions/ 下所有扩展目录，聚合去重所有 Python 依赖。'''
    if not EXTENSIONS_DIR.exists():
        return []
    collected: list[str] = []
    seen: set[str] = set()
    for entry in EXTENSIONS_DIR.iterdir():
        if not entry.is_dir() or entry.name.startswith(('.', '_')):
            continue
        manifest_path = entry / MANIFEST_FILE
        if not manifest_path.exists():
            continue
        for dependency in _read_extension_dependencies(manifest_path):
            if dependency not in seen:
                seen.add(dependency)
                collected.append(dependency)
    return collected


def sync_extension_dependencies() -> None:
    '''读取 pyproject.toml，把收集到的扩展依赖写入 extensions 可选组并写回。'''
    if not PYPROJECT_PATH.exists():
        return
    body = tomlkit.parse(PYPROJECT_PATH.read_text('Utf-8'))
    project = body.setdefault('project', {})
    optional = project.setdefault('optional-dependencies', {})
    optional[EXTENSIONS_EXTRA] = collect_extension_dependencies()
    PYPROJECT_PATH.write_text(tomlkit.dumps(body), encoding='Utf-8')