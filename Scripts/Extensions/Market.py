"""
扩展市场模型与安全解压工具。

市场扩展从 GitHub Release 以源码 zip 分发（不走 PyPI）。本模块提供：
- 注册表条目模型（`MarketExtension` / `MarketRelease`）
- 安装状态模型（`ExtensionInstallState`，写入 `States.toml`）
- 安全解压工具（拒绝路径穿越、符号链接、超限文件）。
"""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, is_zipfile

from nonebot.log import logger
from pydantic import BaseModel, Field

from .Base import ExtensionManifest, parse_manifest
from .Errors import ManifestError

# 单个 zip 解压后允许的最大体积（默认 100 MB）
MAX_ARCHIVE_TOTAL = 100 * 1024 * 1024
# 单个 zip 允许的最大文件数量（防御 zip 炸弹）
MAX_ARCHIVE_FILES = 2048


class MarketRelease(BaseModel):
    """注册表中的单个版本发布条目。"""

    version: str = Field(min_length=1)
    asset_url: str = Field(min_length=1)
    sha256: str = ''
    unibot_version: str = '*'


class MarketExtension(BaseModel):
    """扩展注册表中收录的扩展条目。"""

    id: str = Field(min_length=1, pattern=r'^[A-Za-z0-9_]+$')
    name: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    description: str = ''
    releases: list[MarketRelease] = []

    def latest_release(self) -> MarketRelease | None:
        """返回最新版本发布条目（按 releases 顺序取最后一个）。"""
        return self.releases[-1] if self.releases else None


class ExtensionInstallState(BaseModel):
    """扩展安装状态（统一存放于 `Data/Extension/States.toml`，仅由框架维护）。"""

    source: str = 'local'  # 来源：local / market
    version: str = ''
    sha256: str = ''
    installed_at: str = ''
    repo: str = ''  # 市场来源仓库（owner/repo）
    python_dependencies: list[str] = []


# ===== 安全解压 =====


def _safe_relative(relative: str) -> Path:
    """校验 zip 内相对路径不越界、非绝对路径，返回规范化 Path。"""
    path = Path(relative)
    if path.is_absolute():
        raise ManifestError(f'扩展包内不允许绝对路径：{relative}')
    if '..' in path.parts:
        raise ManifestError(f'扩展包内不允许路径越界：{relative}')
    return path


def safe_extract_zip(archive_data: bytes, target_dir: Path) -> None:
    """
    安全解压 zip 到目标目录。

        拒绝绝对路径、`..` 越界、符号链接/硬链接，并限制解压总大小与文件数量。
        任一步校验失败都会抛出 `ManifestError`，且不向目标目录写入任何文件。
    """
    if not is_zipfile(BytesIO(archive_data)):
        raise ManifestError('扩展包不是有效的 zip 文件！')
    with ZipFile(BytesIO(archive_data)) as zip_file:
        _validate_archive(zip_file)
        zip_file.extractall(target_dir)


def _validate_archive(zip_file: ZipFile) -> None:
    """校验 zip 全部成员：路径安全、符号链接、大小与数量限制。"""
    infos = zip_file.infolist()
    if len(infos) > MAX_ARCHIVE_FILES:
        raise ManifestError(f'扩展包内文件数量过多（{len(infos)} 超过 {MAX_ARCHIVE_FILES}），已拒绝！')
    total_size = 0
    for info in infos:
        _safe_relative(info.filename)
        mode = info.external_attr >> 16
        if mode & 0o170000 == 0o120000:
            raise ManifestError(f'扩展包内不允许符号链接：{info.filename}')
        if not info.is_dir():
            total_size += info.file_size
            if total_size > MAX_ARCHIVE_TOTAL:
                raise ManifestError(f'扩展包解压后体积过大（超过 {MAX_ARCHIVE_TOTAL // (1024 * 1024)} MB），已拒绝！')
    logger.debug(f'扩展包校验通过：{len(infos)} 个文件，约 {total_size} 字节。')


def extract_market_package(archive_data: bytes, target_dir: Path) -> ExtensionManifest:
    """
    安全解压市场扩展包并读取其清单，返回清单信息。

        解压前先校验全部成员安全性，再读取根目录 `Extension.toml` 校验 id。
    """
    # 先整体校验（不改写磁盘），再解压
    if not is_zipfile(BytesIO(archive_data)):
        raise ManifestError('扩展包不是有效的 zip 文件！')
    with ZipFile(BytesIO(archive_data)) as zip_file:
        _validate_archive(zip_file)
        manifest = _read_manifest_from_zip(zip_file)
    target_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(BytesIO(archive_data)) as zip_file:
        zip_file.extractall(target_dir)
    return manifest


def _read_manifest_from_zip(zip_file: ZipFile) -> ExtensionManifest:
    """从 zip 根目录读取并解析 Extension.toml。"""
    manifest_names = [name for name in zip_file.namelist() if name.endswith('Extension.toml')]
    # 只接受根目录下的 Extension.toml（即 <id>/Extension.toml 或根级 Extension.toml）
    if not manifest_names:
        raise ManifestError('扩展包内缺少 Extension.toml 清单！')
    manifest_name = manifest_names[0]
    relative = _safe_relative(manifest_name)
    # 清单必须位于包根目录（根级 Extension.toml 或 <id>/Extension.toml），
    # 不允许嵌套在更深层级
    if len(relative.parts) > 2:
        raise ManifestError('Extension.toml 必须位于扩展包根目录！')
    try:
        content = zip_file.read(manifest_name).decode('Utf-8')
        return parse_manifest(content)
    except ManifestError:
        raise
    except Exception as error:
        raise ManifestError(f'扩展包清单解析失败：{error}') from error
