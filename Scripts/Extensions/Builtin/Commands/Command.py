"""内置扩展：控制台命令指令。"""

from typing import override

from nonebot_plugin_alconna import Match
from nonebot_plugin_uninfo import Uninfo

from Scripts import Globals
from Scripts.Config import config
from Scripts.Extensions import Command, Extension
from Scripts.Logging import logger
from Scripts.Messages import messages
from Scripts.Utils import get_permission, turn_message_text

# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(id='Command', name='控制台命令', version='1.0.0', types=('command',))


@extension.register_command
class CommandCommand(Command):
    """向指定服务器发送控制台命令。"""

    name = 'command'
    description = '向指定服务器发送控制台命令。'
    usage = '/command <服务器名称> <命令>'

    @override
    def declare(self) -> None:
        self.register_arg('server', str, description='服务器名称')
        self.register_arg('command', str, description='要执行的命令', multi=True)

    @override
    async def handler(self, session: Uninfo, server: Match[str], command: Match[list[str]]):
        if not get_permission(session):
            return messages.commands.command.no_permission
        command_string = ' '.join(command.result)
        return await turn_message_text(self.command_handler(server.result, command_string))

    def parse_command(self, command: str):
        """按黑白名单过滤允许发送的控制台命令。"""
        if config.command_minecraft_whitelist:
            if any(command.startswith(item) for item in config.command_minecraft_whitelist):
                return command
            return None
        if any(command.startswith(item) for item in config.command_minecraft_blacklist):
            return None
        return command

    async def command_handler(self, server_flag, command):
        server_service = Globals.server_service
        if server_service is None:
            yield messages.commands.command.no_server
            return
        if not (parsed_command := self.parse_command(command)):
            yield messages.commands.command.command_forbidden.format(command=command)
            return
        if server_flag == '*':
            if not server_service.servers:
                yield messages.commands.command.no_server
                return
            yield messages.commands.command.send_all_title
            for name, bot in server_service.servers.items():
                try:
                    result = await bot.send_rcon_command(command=parsed_command)
                    reply = result if result else messages.commands.command.no_return
                    yield messages.commands.command.send_result.format(name=name, result=reply)
                except Exception as error:
                    logger.warning(f'向服务器 [{name}] 发送指令失败：{error}')
                    yield messages.commands.command.send_failed.format(name=name)
            return
        bot = server_service.get_server(server_flag)
        if bot is None:
            yield messages.commands.command.server_not_found.format(server_flag=server_flag)
            return
        try:
            result = await bot.send_rcon_command(command=parsed_command)
            reply = result if result else messages.commands.command.no_return
            yield messages.commands.command.send_success.format(server=bot.self_id, result=reply)
        except Exception as error:
            yield messages.commands.command.send_error.format(server_flag=server_flag, error=error)
