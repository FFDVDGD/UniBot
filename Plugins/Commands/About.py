from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from Scripts.Extensions import Command, SubCommand
from Scripts.Globals import render_template
from Scripts.Managers import version_manager
from Scripts.Messages import messages
from Scripts.Utils import turn_message_text

__plugin_meta__ = PluginMetadata(
    name='关于信息',
    description='展示 UniBot 的版本、更新状态与项目信息。',
    usage='.about',
)

logger.debug('加载命令 About 完毕！')


class AboutCommand(Command):
    '''查看关于信息。'''

    name = 'about'
    description = '查看关于信息。'
    usage = '.about'

    class Check(SubCommand['AboutCommand']):
        '''检测是否有新版本。'''

        name = 'check'
        description = '检测是否有新版本'

        async def handler(self):
            '''主动拉取最新版本并反馈检测结果'''
            return await turn_message_text(self.parent.check_handler())

        async def image_handler(self) -> bytes:
            '''拉取最新版本后渲染关于信息为图片（由框架在图像模式发送）。'''
            await version_manager.fetch_latest()
            return await self.parent._render_about()

    async def handler(self):
        return await turn_message_text(self.about_handler())

    async def image_handler(self) -> bytes:
        '''渲染关于信息为图片，返回 PNG 字节（由框架在图像模式发送）。'''
        return await self._render_about()

    async def _render_about(self) -> bytes:
        '''渲染当前版本信息的模板图片。'''
        return await render_template(
            'About', (500, 0),
            version=version_manager.version, has_update=version_manager.check_update(),
        )

    async def about_handler(self):
        if version_manager.check_update():
            yield messages.commands.about.version_with_update.format(version=version_manager.version)
            yield messages.commands.about.document_line
            yield messages.commands.about.repo_line
            yield messages.commands.about.invite_line
            return
        yield messages.commands.about.version_latest.format(version=version_manager.version)
        yield messages.commands.about.document_line
        yield messages.commands.about.repo_line
        yield messages.commands.about.invite_line

    async def check_handler(self):
        if await version_manager.fetch_latest():
            if version_manager.check_update():
                yield messages.commands.about.check_has_update.format(
                    latest=version_manager.latest_version, version=version_manager.version
                )
                return
            yield messages.commands.about.check_latest.format(version=version_manager.version)
            return
        yield messages.commands.about.check_failed
