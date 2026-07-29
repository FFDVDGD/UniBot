from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Command
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers.Version import version_manager
from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

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
    yield f'当前版本为 {version_manager.version}，{'发现新版本，请及时更新！' if version_manager.check_update() else '已是最新版本！'}'
    yield '\n项目文档：https://github.com/MineJPGcraft/UniBot/blob/main/README.md'
    yield '项目地址 https://github.com/MineJPGcraft/UniBot'
    yield '欢迎加入 QQ 交流群 962802248，对这个项目感兴趣不妨点个 Star 吧！'


async def check_handler():
    if await version_manager.fetch_latest():
        if version_manager.check_update():
            yield f'发现新版本 {version_manager.latest_version}，当前版本为 {version_manager.version}，请及时更新！'
            return
        yield f'当前已是最新版本 {version_manager.version}！'
        return
    yield '检测失败，请检查网络稍后再试！'
