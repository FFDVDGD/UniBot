from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Command
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers import version_manager
from Scripts.Messages import messages
from Scripts.Rules import command_group_rule
from Scripts.Utils import turn_message_text

__plugin_meta__ = PluginMetadata(
    name='关于信息',
    description='展示 UniBot 的版本、更新状态与项目信息。',
    usage='.about',
)

logger.debug('加载命令 About 完毕！')

matcher = (
    Command('about', '查看关于信息。')
    .subcommand('check #检测是否有新版本')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.assign('$main')
async def handle():
    if config.image.mode:
        image = await render_template(
            'About', (500, 0),
            version=version_manager.version, has_update=version_manager.check_update(),
        )
        await matcher.finish(UniMessage(Image(raw=image)))
    message = await turn_message_text(about_handler())
    await matcher.finish(message)


@matcher.assign('check')
async def handle_check():
    '''主动拉取最新版本并反馈检测结果'''
    if config.image.mode:
        await version_manager.fetch_latest()
        image = await render_template(
            'About', (500, 0),
            version=version_manager.version, has_update=version_manager.check_update(),
        )
        await matcher.finish(UniMessage(Image(raw=image)))
    message = await turn_message_text(check_handler())
    await matcher.finish(message)


async def about_handler():
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


async def check_handler():
    if await version_manager.fetch_latest():
        if version_manager.check_update():
            yield messages.commands.about.check_has_update.format(
                latest=version_manager.latest_version, version=version_manager.version
            )
            return
        yield messages.commands.about.check_latest.format(version=version_manager.version)
        return
    yield messages.commands.about.check_failed
