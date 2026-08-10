"""
扩展依赖收集测试。

验证方案：未启用的扩展不参与依赖收集（不写入 pyproject.toml 的 extensions 组），
但已写入的既有依赖会保留不删；重复同步幂等。
"""

import textwrap
from pathlib import Path

from Scripts.Extensions import Dependencies


def _write_extension(root: Path, name: str, python_deps: list[str]) -> None:
    """在临时 Extensions/ 下写入一个扩展目录及其 Extension.toml。"""
    ext_dir = root / 'Extensions' / name
    ext_dir.mkdir(parents=True)
    deps = ', '.join(f'"{dep}"' for dep in python_deps)
    (ext_dir / 'Extension.toml').write_text(
        textwrap.dedent(
            f"""
            [extension]
            id = "{name}"

            [dependencies]
            python = [{deps}]
            """
        ),
        encoding='Utf-8',
    )


def _write_enabled_config(root: Path, disabled: list[str]) -> None:
    """写入 Config/Extensions.toml，将指定扩展标记为禁用。"""
    config_dir = root / 'Config'
    config_dir.mkdir(parents=True)
    lines = []
    for name in disabled:
        lines.append(f'[{name}]')
        lines.append('enabled = false')
    (config_dir / 'Extensions.toml').write_text('\n'.join(lines), encoding='Utf-8')


def _write_pyproject(root: Path, extensions: list[str]) -> None:
    """写入带 extensions 可选组的 pyproject.toml。"""
    deps = ', '.join(f'"{dep}"' for dep in extensions)
    (root / 'pyproject.toml').write_text(
        textwrap.dedent(
            f"""
            [project]
            name = "test"

            [project.optional-dependencies]
            extensions = [{deps}]
            """
        ),
        encoding='Utf-8',
    )


def _setup(tmp_path: Path, monkeypatch) -> None:
    """把 Dependencies 模块的路径常量指向临时目录。"""
    monkeypatch.setattr(Dependencies, 'EXTENSIONS_DIR', tmp_path / 'Extensions')
    monkeypatch.setattr(
        Dependencies, 'CONFIG_EXTENSIONS_FILE', tmp_path / 'Config' / 'Extensions.toml'
    )
    monkeypatch.setattr(Dependencies, 'PYPROJECT_PATH', tmp_path / 'pyproject.toml')


# ===== 依赖收集 =====


class TestCollectExtensionDependencies:
    def test_disabled_extension_dependencies_skipped(self, tmp_path, monkeypatch):
        """未启用的扩展不参与依赖收集。"""
        _write_extension(tmp_path, 'EnabledExt', ['dep-a', 'dep-common'])
        _write_extension(tmp_path, 'DisabledExt', ['dep-b', 'dep-common'])
        _write_enabled_config(tmp_path, ['DisabledExt'])
        _setup(tmp_path, monkeypatch)

        collected = Dependencies.collect_extension_dependencies()
        assert sorted(collected) == ['dep-a', 'dep-common']

    def test_missing_enabled_config_defaults_to_enabled(self, tmp_path, monkeypatch):
        """Config/Extensions.toml 缺失时默认全部启用（与 Loader 语义一致）。"""
        _write_extension(tmp_path, 'ExtA', ['dep-a'])
        _write_extension(tmp_path, 'ExtB', ['dep-b'])
        _setup(tmp_path, monkeypatch)

        collected = Dependencies.collect_extension_dependencies()
        assert sorted(collected) == ['dep-a', 'dep-b']


# ===== 同步写回 pyproject.toml =====


class TestSyncExtensionDependencies:
    def test_keeps_existing_and_appends_enabled_only(self, tmp_path, monkeypatch):
        """既有依赖保留，仅追加已启用扩展的依赖，未启用扩展依赖不写入。"""
        _write_extension(tmp_path, 'EnabledExt', ['dep-a'])
        _write_extension(tmp_path, 'DisabledExt', ['dep-b'])
        _write_enabled_config(tmp_path, ['DisabledExt'])
        _write_pyproject(tmp_path, ['old-dep'])
        _setup(tmp_path, monkeypatch)

        Dependencies.sync_extension_dependencies()

        body = (tmp_path / 'pyproject.toml').read_text('Utf-8')
        assert 'old-dep' in body
        assert 'dep-a' in body
        assert 'dep-b' not in body

    def test_sync_is_idempotent(self, tmp_path, monkeypatch):
        """重复同步不会重复追加依赖。"""
        _write_extension(tmp_path, 'EnabledExt', ['dep-a'])
        _write_pyproject(tmp_path, ['old-dep'])
        _setup(tmp_path, monkeypatch)

        Dependencies.sync_extension_dependencies()
        Dependencies.sync_extension_dependencies()

        body = (tmp_path / 'pyproject.toml').read_text('Utf-8')
        assert body.count('dep-a') == 1
