import asyncio
import shutil
import tempfile
from pathlib import Path

from Scripts.Logging import logger
from Scripts.Network import github_download, request

from .Config import config_manager

# Release 资产中 UniBot.zip 的资源名
UNIBOT_ZIP_ASSET = 'UniBot.zip'
LATEST_RELEASE_API = 'https://api.github.com/repos/MineJPGcraft/UniBot/releases/latest'


class VersionManager:
    """版本管理器，负责读取当前版本、检测并更新到 GitHub 上的最新发布版本。"""

    version: str = ''
    latest_version: str | None = None
    latest_asset_url: str | None = None

    def check_update(self) -> bool:
        """当前版本是否落后于最新版本。"""
        return self.latest_version is not None and self.latest_version != self.version

    async def init(self):
        """记录当前版本，并在后台异步拉取最新版本。"""
        self.version = str(config_manager.version)
        logger.info(f'监测到当前为 {self.version} 版本。')
        await self.fetch_latest()

    async def fetch_latest(self) -> bool:
        """从 GitHub 拉取最新发布版本，成功返回 True。"""
        latest_data = await request(LATEST_RELEASE_API)
        if not latest_data:
            logger.warning('获取最新版本失败，请检查网络稍后再试！')
            return False
        self.latest_version = str(latest_data.get('tag_name', ''))
        if not self.latest_version:
            logger.warning('获取最新版本失败：返回数据缺少版本信息！')
            return False
        self.latest_asset_url = self.find_bot_asset(latest_data)
        if self.check_update():
            logger.info(f'发现新版本 {self.latest_version}，当前版本为 {self.version}！')
        return True

    @staticmethod
    def find_bot_asset(release_data: dict) -> str | None:
        """从 Release 数据中查找 UniBot.zip 资产的下载地址。"""
        for asset in release_data.get('assets', []) or []:
            if asset.get('name') == UNIBOT_ZIP_ASSET:
                return asset.get('browser_download_url')
        return None

    async def update(self) -> str | None:
        """从 GitHub Release 下载最新代码并替换 Scripts 目录，成功返回 None，失败返回错误信息。"""
        if not await self.fetch_latest():
            return '更新失败，请检查网络稍后再试！'
        asset_url = self.latest_asset_url
        if not asset_url:
            return '更新失败，最新版本缺少 UniBot.zip 资源！'
        archive = await github_download(asset_url)
        if archive is None:
            return '更新失败，下载 UniBot.zip 失败，请检查网络稍后再试！'
        error_message = await asyncio.to_thread(self._apply_update, archive.getvalue())
        if error_message:
            logger.warning(f'更新失败：{error_message}')
            return error_message
        return None

    def _apply_update(self, archive_data: bytes) -> str | None:
        """安全解压 UniBot.zip 并替换 Scripts 目录，成功返回 None，失败返回错误信息。"""
        from Scripts.Utils import safe_extract_zip

        scripts_dir = Path('Scripts')
        try:
            with tempfile.TemporaryDirectory() as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                safe_extract_zip(archive_data, temp_dir)
                source = temp_dir / 'Scripts'
                if not source.is_dir():
                    return '压缩包内缺少核心目录，已取消更新！'
                backup_dir = scripts_dir.with_name('Scripts.bak')
                shutil.rmtree(backup_dir, ignore_errors=True)
                if scripts_dir.exists():
                    scripts_dir.rename(backup_dir)
                try:
                    source.replace(scripts_dir)
                except Exception:
                    if backup_dir.exists() and not scripts_dir.exists():
                        backup_dir.rename(scripts_dir)
                    raise
                shutil.rmtree(backup_dir, ignore_errors=True)
            logger.success('已将核心代码更新为最新版本！')
            return None
        except Exception as error:
            logger.warning(f'更新解压失败：{error}')
            return '更新失败，请查看控制台日志！'


version_manager = VersionManager()
