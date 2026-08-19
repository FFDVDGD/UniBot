from typing import override

from Scripts.Extensions import Command, Extension, SubCommand

extension = Extension(id='FakeExt', name='假扩展', version='1.0.0', types=('command',))


@extension.register_command
class FakeCommand(Command):
    name = 'fake'
    description = '假命令'

    class Ping(SubCommand['FakeCommand']):
        name = 'ping'
        description = '子命令'

        @override
        async def handler(self):
            return 'pong'
