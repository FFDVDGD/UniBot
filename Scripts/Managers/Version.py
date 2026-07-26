import asyncio

from nonebot.log import logger

from Scripts.Network import request
from .Environment import environment_manager

LATEST_RELEASE_API = 'https://api.github.com/repos/Minecraft-UniBot/UniBot/releases/latest'


class VersionManager:
    '''版本管理器，负责读取当前版本并检测 GitHub 上的最新发布版本'''

    version: str = ''
    latest_version: str | None = None

    def check_update(self) -> bool:
        '''当前版本是否落后于最新版本'''
        if self.latest_version is None:
            return False
        return self.latest_version != self.version

    async def init(self):
        '''记录当前版本，并在后台异步拉取最新版本'''
        self.version = environment_manager.version
        logger.info(f'监测到当前为 {self.version} 版本。')
        asyncio.create_task(self.fetch_latest())

    async def fetch_latest(self) -> bool:
        '''从 GitHub 拉取最新发布版本，成功返回 True'''
        latest_data = await request(LATEST_RELEASE_API)
        if not latest_data:
            logger.warning('获取最新版本失败，请检查网络稍后再试！')
            return False
        self.latest_version = str(latest_data.get('tag_name', '')).lstrip('v')
        if not self.latest_version:
            logger.warning('获取最新版本失败：返回数据缺少版本信息！')
            return False
        if self.check_update():
            logger.info(f'发现新版本 {self.latest_version}，当前版本为 {self.version}！')
        else:
            logger.info(f'当前已是最新版本 {self.version}！')
        return True


version_manager = VersionManager()
