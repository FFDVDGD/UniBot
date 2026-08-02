from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import Command, Match

from Scripts.Config import config
from Scripts.Managers import server_manager
from Scripts.Messages import messages
from Scripts.Rules import command_group_rule
from Scripts.Utils import get_permission, turn_message_text

__plugin_meta__ = PluginMetadata(
    name='控制台命令',
    description='向指定 Minecraft 服务器发送经过权限校验的控制台命令。',
    usage='.command <服务器名称> <命令>',
)

matcher = (
    Command('command <server#服务器名称:str> <command#要执行的命令:str+>', '向指定服务器发送控制台命令。')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle(session: Uninfo, server: Match[str], command: Match[list[str]]):
    if not get_permission(session):
        await matcher.finish(messages.commands.command.no_permission)
    if not command.available:
        await matcher.finish(messages.commands.command.invalid_param)
    command_string = ' '.join(command.result)
    message = await turn_message_text(command_handler(server.result, command_string))
    await matcher.finish(message)


def parse_command(command: str):
    if config.command_minecraft_whitelist:
        for enabled_command in config.command_minecraft_whitelist:
            if command.startswith(enabled_command):
                return command
        return None
    for disabled_command in config.command_minecraft_blacklist:
        if command.startswith(disabled_command):
            return None
    return command


async def command_handler(server_flag, command):
    if not (parsed_command := parse_command(command)):
        yield messages.commands.command.command_forbidden.format(command=command)
        return
    if server_flag == '*':
        if not server_manager.servers:
            yield messages.commands.command.no_server
            return
        for name, bot in server_manager.servers.items():
            yield messages.commands.command.send_all_title
            try:
                result = await bot.send_rcon_command(command=parsed_command)
                reply = result if result else messages.commands.command.no_return
                yield messages.commands.command.send_result.format(name=name, result=reply)
            except Exception as error:
                logger.warning(f'向服务器 [{name}] 发送指令失败：{error}')
                yield messages.commands.command.send_failed.format(name=name)
        return
    bot = server_manager.get_server(server_flag)
    if bot is None:
        yield messages.commands.command.server_not_found.format(server_flag=server_flag)
        return
    try:
        result = await bot.send_rcon_command(command=parsed_command)
        reply = result if result else messages.commands.command.no_return
        yield messages.commands.command.send_success.format(server=bot.self_id, result=reply)
    except Exception as error:
        yield messages.commands.command.send_error.format(server_flag=server_flag, error=error)
