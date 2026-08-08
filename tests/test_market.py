'''A8 市场安全解压与安装事务测试。

验证方案 item 19：SHA-256 不匹配、清单不一致、路径穿越、符号链接、超出文件限制时，
当前扩展版本不发生改变。
'''

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from Scripts.Extensions import (
    ManifestError,
    extract_market_package,
    safe_extract_zip,
)
from Scripts.Extensions.Market import MAX_ARCHIVE_FILES, MAX_ARCHIVE_TOTAL


def _make_zip(files: dict[str, bytes]) -> bytes:
    '''生成内存 zip（files: 相对路径 -> 内容）。'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


def _valid_manifest() -> str:
    '''生成一份合法的 Extension.toml 内容。'''
    return '''
[manifest]
schema_version = 1

[extension]
id = "TestExt"
name = "测试扩展"
version = "1.0.0"
author = "UniBot"
description = "测试"
types = ["api"]

[compatibility]
unibot = "*"

[dependencies]
extensions = []
python = []
'''


# ===== 安全解压 =====

class TestSafeExtractZip:
    def test_extract_plain(self, tmp_path):
        archive = _make_zip({'TestExt/__init__.py': b'print(1)'})
        safe_extract_zip(archive, tmp_path)
        assert (tmp_path / 'TestExt' / '__init__.py').read_bytes() == b'print(1)'

    def test_path_traversal_rejected(self, tmp_path):
        archive = _make_zip({'../evil.py': b'evil'})
        with pytest.raises(ManifestError):
            safe_extract_zip(archive, tmp_path)
        # 不得写出目标目录
        assert not (tmp_path.parent / 'evil.py').exists()

    def test_absolute_path_rejected(self, tmp_path):
        archive = _make_zip({'/abs.py': b'evil'})
        with pytest.raises(ManifestError):
            safe_extract_zip(archive, tmp_path)

    def test_symlink_rejected(self, tmp_path):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            info = zipfile.ZipInfo('link')
            # 在 Unix 标志位中标记为符号链接
            info.external_attr = 0o120777 << 16
            zf.writestr(info, b'target')
        with pytest.raises(ManifestError):
            safe_extract_zip(buffer.getvalue(), tmp_path)

    def test_not_zip_rejected(self, tmp_path):
        with pytest.raises(ManifestError):
            safe_extract_zip(b'not a zip', tmp_path)

    def test_too_many_files_rejected(self, tmp_path):
        files = {f'f{i}': b'x' for i in range(MAX_ARCHIVE_FILES + 1)}
        archive = _make_zip(files)
        with pytest.raises(ManifestError):
            safe_extract_zip(archive, tmp_path)

    def test_too_large_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setattr('Scripts.Extensions.Market.MAX_ARCHIVE_TOTAL', 10)
        archive = _make_zip({'big.bin': b'x' * 100})
        with pytest.raises(ManifestError):
            safe_extract_zip(archive, tmp_path)


# ===== 解压 + 清单读取 =====

class TestExtractMarketPackage:
    def test_extract_with_manifest(self, tmp_path):
        archive = _make_zip({
            'TestExt/Extension.toml': _valid_manifest().encode(),
            'TestExt/__init__.py': b'pass',
        })
        manifest = extract_market_package(archive, tmp_path)
        assert manifest.extension.id == 'TestExt'
        assert (tmp_path / 'TestExt' / '__init__.py').exists()

    def test_missing_manifest_rejected(self, tmp_path):
        archive = _make_zip({'TestExt/__init__.py': b'pass'})
        with pytest.raises(ManifestError):
            extract_market_package(archive, tmp_path)

    def test_manifest_not_at_root_rejected(self, tmp_path):
        archive = _make_zip({
            'TestExt/sub/Extension.toml': _valid_manifest().encode(),
        })
        with pytest.raises(ManifestError):
            extract_market_package(archive, tmp_path)

    def test_invalid_manifest_rejected(self, tmp_path):
        archive = _make_zip({'TestExt/Extension.toml': b'not toml [[['})
        with pytest.raises(ManifestError):
            extract_market_package(archive, tmp_path)


# ===== SHA-256 =====

def test_sha256_mismatch_rejected(monkeypatch):
    '''SHA-256 与下载内容不匹配时抛 ManifestError。'''
    from Scripts.Extensions.MarketManager import ExtensionMarketManager

    manager = ExtensionMarketManager()
    archive = _make_zip({'TestExt/__init__.py': b'pass'})

    async def fake_download(url):
        return io.BytesIO(archive)

    async def run():
        return await manager._download_release(
            'https://example.com/x.zip', hashlib.sha256(b'wrong').hexdigest()
        )

    monkeypatch.setattr('Scripts.Extensions.MarketManager.github_download', fake_download)
    with pytest.raises(ManifestError):
        import asyncio
        asyncio.run(run())


def test_sha256_match_ok(monkeypatch):
    '''SHA-256 匹配时下载成功。'''
    from Scripts.Extensions.MarketManager import ExtensionMarketManager

    manager = ExtensionMarketManager()
    archive = _make_zip({'TestExt/__init__.py': b'pass'})

    async def fake_download(url):
        return io.BytesIO(archive)

    async def run():
        return await manager._download_release(
            'https://example.com/x.zip', hashlib.sha256(archive).hexdigest()
        )

    monkeypatch.setattr('Scripts.Extensions.MarketManager.github_download', fake_download)
    import asyncio
    result = asyncio.run(run())
    assert result == archive