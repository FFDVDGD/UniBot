from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Match

from Scripts.Extensions import Command, command_manager
from Scripts.Globals import render_template
from Scripts.Managers import config_manager
from Scripts.Messages import messages
from Scripts.Utils import turn_message_text

__plugin_meta__ = PluginMetadata(
    name='命令帮助',
    description='列出可用命令或展示指定命令的详细帮助。',
    usage='.help [命令名称]',
)


def get_enabled_nodes() -> list[Command]:
    '''获取 pyproject.toml 中已启用且已登记的内置命令节点。'''
    enabled_modules = {
        plugin.get('module_name', plugin) if isinstance(plugin, dict) else plugin
        for plugin in config_manager.nonebot_config.get('plugins', [])
        if (plugin.get('enabled', True) if isinstance(plugin, dict) else True)
        and (plugin.get('module_name', plugin) if isinstance(plugin, dict) else plugin).startswith('Plugins.Commands.')
    }
    nodes = []
    for command_id, command in command_manager.get_command_nodes().items():
        if not command_id.startswith('builtin:'):
            continue
        module_name = f'Plugins.Commands.{command.name.capitalize()}'
        if module_name in enabled_modules:
            nodes.append(command)
    return nodes


def get_node(name: str) -> Command | None:
    '''从已登记命令实例中查找指定名称的命令。'''
    for command in get_enabled_nodes():
        if command.name == name:
            return command
    return None


def gen_usage(command: Command) -> str:
    '''根据结构化命令自动生成用法字符串（含子命令、参数）。'''
    parts = [command.name]
    for argument in command.arguments:
        display = f'<{argument.name}>' if argument.required else f'[{argument.name}]'
        parts.append(display)
    return ' '.join(parts)


def sub_usage(command: Command) -> str:
    '''根据子命令实例生成用法字符串。'''
    parts = [command.name]
    for argument in command.arguments:
        display = f'<{argument.name}>' if argument.required else f'[{argument.name}]'
        parts.append(display)
    return ' '.join(parts)


def node_args(command: Command) -> list[dict]:
    '''提取命令参数（含描述）用于图片渲染。'''
    return [
        {'name': argument.name, 'notice': argument.description}
        for argument in command.arguments
        if argument.description
    ]


class HelpCommand(Command):
    '''查看所有可用命令的帮助信息。'''

    name = 'help'
    description = '查看所有可用命令的帮助信息。'
    usage = '.help [命令名称]'

    def declare(self) -> None:
        self.register_option('command', str, default=None, description='命令名称')

    async def handler(self, command: Match[str]):
        if command.available:
            return await turn_message_text(self.detailed_handler(command.result))
        return await turn_message_text(self.help_handler())

    async def image_handler(self, command: Match[str]) -> bytes:
        '''渲染帮助信息为图片，返回 PNG 字节（由框架在图像模式发送）。'''
        if command.available:
            detail = self.get_command_detail(command.result)
            return await render_template('Help', (600, 0), detail=detail, commands=None)
        commands = self.get_commands_list()
        return await render_template('Help', (600, 0), detail=None, commands=commands)

    def get_commands_list(self) -> list[dict]:
        '''构建命令列表数据用于图片渲染'''
        commands = []
        for command in get_enabled_nodes():
            usage = command.usage or gen_usage(command)
            description = command.description or ''
            sub_list = []
            for index, subcommand in enumerate(command.subcommands):
                branch = '└─' if index == len(command.subcommands) - 1 else '├─'
                sub_desc = f' — {subcommand.description}' if subcommand.description else ''
                sub_list.append(f'{branch} {subcommand.name}{sub_desc}')
            commands.append({'usage': usage, 'description': description, 'subcommands': sub_list})
        return commands

    def get_command_detail(self, name: str) -> dict | None:
        '''构建命令详情数据用于图片渲染'''
        command = get_node(name)
        if command is None:
            return None
        sub_list = [
            {'name': sub.name, 'usage': sub_usage(sub), 'description': sub.description or ''}
            for sub in command.subcommands
        ]
        return {
            'name': name,
            'usage': command.usage or gen_usage(command),
            'description': command.description or '',
            'args': node_args(command),
            'subcommands': sub_list,
        }

    def help_handler(self):
        yield messages.commands.help.title
        for command in get_enabled_nodes():
            usage = command.usage or gen_usage(command)
            description = command.description or ''
            yield f'    {usage} — {description}'
            for index, subcommand in enumerate(command.subcommands):
                branch = '└─' if index == len(command.subcommands) - 1 else '├─'
                subcommand_description = f' — {subcommand.description}' if subcommand.description else ''
                yield f'    {branch} {subcommand.name}{subcommand_description}'
        yield messages.commands.help.footnote

    def detailed_handler(self, name: str):
        command = get_node(name)
        if command is None:
            yield messages.commands.help.not_found.format(name=name)
            return
        yield messages.commands.help.detail_title.format(name=name)
        yield f'    {messages.commands.help.detail_usage.format(usage=command.usage or gen_usage(command))}'
        if command.description:
            yield f'    {messages.commands.help.detail_description.format(description=command.description)}'
        notices = node_args(command)
        if notices:
            yield f'    {messages.commands.help.detail_args_title}'
            for arg in notices:
                yield f'        {messages.commands.help.arg_line.format(name=arg["name"], notice=arg["notice"])}'
        if not command.subcommands:
            return
        yield f'    {messages.commands.help.detail_subcommands_title}'
        for index, subcommand in enumerate(command.subcommands):
            branch = '└─' if index == len(node.subcommands) - 1 else '├─'
            continuation = '    ' if index == len(node.subcommands) - 1 else '│   '
            subcommand_description = f' — {subcommand.description}' if subcommand.description else ''
            yield f'        {branch} {sub_usage(subcommand)}{subcommand_description}'
            for arg in subcommand.arguments:
                if arg.description:
                    yield f'        {continuation}    {messages.commands.help.arg_line.format(name=arg.name, notice=arg.description)}'
