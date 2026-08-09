'''内置扩展：服务器列表指令。'''

from typing import override

from Scripts.Extensions import Command, Extension
from Scripts.Globals import render_template
from Scripts.Managers import server_manager
from Scripts.Messages import messages
from Scripts.Utils import turn_message_text

# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(id='Server', name='服务器列表', version='1.0.0', types=('command',))


@extension.register_command
class ServerCommand(Command):
    '''查看已连接的服务器列表。'''

    name = 'server'
    description = '查看已连接的服务器列表。'
    usage = '.server'

    @override
    async def handler(self):
        return await turn_message_text(self.server_handler())

    @override
    async def image_handler(self) -> bytes:
        '''渲染服务器列表为图片，返回 PNG 字节（由框架在图像模式发送）。'''
        servers = [
            {'name': name, 'index': index}
            for index, name in enumerate(server_manager.servers.keys())
        ]
        return await render_template('Server', (500, 0), servers=servers)

    async def server_handler(self):
        if not server_manager.servers:
            yield messages.commands.server.no_server
            return
        for index, name in enumerate(server_manager.servers.keys()):
            yield messages.commands.server.server_line.format(index=index, name=name)