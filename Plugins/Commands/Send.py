from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Command, Match
from nonebot_plugin_uninfo import Uninfo

from Scripts.Managers import data_manager, server_manager
from Scripts.Utils import get_platform_name, get_player_name
from Scripts.Rules import command_group_rule

__plugin_meta__ = PluginMetadata(
    name='消息发送',
    description='将聊天平台中的消息广播到已连接的 Minecraft 服务器。',
    usage='.send <消息内容>',
)

matcher = (
    Command('send <message#要发送的消息内容:str+>', '向已连接的服务器发送消息。')
    .alias('mc')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle(session: Uninfo, message: Match[list[str]]):
    if not message.available:
        await matcher.finish('参数错误，请检查命令格式！')
    message_text = ' '.join(message.result).strip()
    if not message_text:
        await matcher.finish('参数错误，请检查命令格式！')
    user_id = str(session.user.id)
    user_name = session.user.name or get_player_name(str(session.user.name))
    platform_name = get_platform_name(session.scope)
    if name := data_manager.players.get(user_id, (user_name,))[0]:
        await server_manager.broadcast(f'[{platform_name}]<{name}> {message_text}')
        await matcher.finish(f'已向服务器发送消息：{message_text}。')
    await server_manager.broadcast(f'[{platform_name}]<未知用户> {message_text}')
    await matcher.finish('未找到你的玩家名称，请绑定后再试！')
