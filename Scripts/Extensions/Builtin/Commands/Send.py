"""内置扩展：消息发送指令。"""

from typing import override

from nonebot_plugin_alconna import Match
from nonebot_plugin_uninfo import Uninfo

from Scripts import Globals
from Scripts.Extensions import Command, Extension
from Scripts.Messages import messages
from Scripts.Utils import get_platform_name

# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(id='Send', name='消息发送', version='1.0.0', types=('command',))


@extension.register_command
class SendCommand(Command):
    """向已连接的服务器发送消息。"""

    name = 'send'
    description = '向已连接的服务器发送消息。'
    usage = '.send <消息内容>'
    aliases = ('mc',)

    @override
    def declare(self) -> None:
        self.register_arg('message', str, description='要发送的消息内容', multi=True)

    @override
    async def handler(self, session: Uninfo, message: Match[list[str]]):
        if not message.available:
            return messages.commands.send.param_error
        message_text = ' '.join(message.result).strip()
        if not message_text:
            return messages.commands.send.param_error
        user_id = str(session.user.id)
        platform_name = get_platform_name(session.scope)
        player_service, server_service = Globals.player_service, Globals.server_service
        if server_service is None:
            return messages.commands.send.not_bound
        if (
            name := player_service.players.get(user_id, (session.user.name,))[0]
            if player_service
            else session.user.name
        ):
            await server_service.broadcast(f'[{platform_name}]<{name}> {message_text}')
            return messages.commands.send.sent.format(content=message_text)
        await server_service.broadcast(f'[{platform_name}]<未知用户> {message_text}')
        return messages.commands.send.not_bound
