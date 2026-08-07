'''内置指令重构测试：register_builtin_commands 收集与结构验证（验证点 3、4、11）。'''

import importlib
from types import SimpleNamespace

import pytest

from Scripts.Extensions import Command, CommandError, CommandManager, SubCommand


PLUGINS = [
    {'module_name': 'Plugins.Commands.About', 'enabled': True},
    {'module_name': 'Plugins.Commands.Bound', 'enabled': True},
    {'module_name': 'Plugins.Commands.Command', 'enabled': True},
    {'module_name': 'Plugins.Commands.Help', 'enabled': True},
    {'module_name': 'Plugins.Commands.List', 'enabled': True},
    {'module_name': 'Plugins.Commands.Luck', 'enabled': True},
    {'module_name': 'Plugins.Commands.Send', 'enabled': True},
    {'module_name': 'Plugins.Commands.Server', 'enabled': True},
    {'module_name': 'Plugins.Expand.Ai', 'enabled': False},
]


@pytest.fixture(autouse=True)
def _configure_plugins():
    '''为测试注入内置插件配置，结束后还原。'''
    from Scripts.Managers import config_manager

    original = config_manager.nonebot_config
    config_manager.nonebot_config = {'plugins': PLUGINS}
    yield
    config_manager.nonebot_config = original


def _make_manager(monkeypatch) -> CommandManager:
    '''构建管理器，并用假模块替换真实内置命令模块避免插件加载时序问题。'''
    manager = CommandManager()

    def fake_import(module_name: str):
        module = SimpleNamespace()
        if module_name == 'Plugins.Commands.About':
            module.AboutCommand = _AboutCommand
        elif module_name == 'Plugins.Commands.Bound':
            module.BoundCommand = _BoundCommand
        elif module_name == 'Plugins.Commands.Command':
            module.CommandCommand = _ConsoleCommand
        elif module_name == 'Plugins.Commands.Help':
            module.HelpCommand = _HelpCommand
        elif module_name == 'Plugins.Commands.List':
            module.ListCommand = _ListCommand
        elif module_name == 'Plugins.Commands.Luck':
            module.LuckCommand = _LuckCommand
        elif module_name == 'Plugins.Commands.Send':
            module.SendCommand = _SendCommand
        elif module_name == 'Plugins.Commands.Server':
            module.ServerCommand = _ServerCommand
        else:
            return SimpleNamespace()
        return module

    command_module = importlib.import_module('Scripts.Extensions.Command')

    monkeypatch.setattr(command_module.importlib, 'import_module', fake_import)
    manager.register_builtin_commands()
    return manager


# ===== 假命令类 =====

class _AboutCommand(Command):
    name = 'about'
    description = '关于'

    class Check(SubCommand):
        name = 'check'
        description = '检查更新'


class _BoundCommand(Command):
    name = 'bound'
    description = '绑定'

    class List(SubCommand):
        name = 'list'
        description = '列出'

    class Query(SubCommand):
        name = 'query'
        description = '查询'

    class Remove(SubCommand):
        name = 'remove'
        description = '移除'

    class Append(SubCommand):
        name = 'append'
        description = '添加'


class _ConsoleCommand(Command):
    name = 'command'
    description = '执行命令'

    def declare(self) -> None:
        self.register_arg('server', str, description='服务器')
        self.register_arg('command', str, description='命令', multi=True)


class _HelpCommand(Command):
    name = 'help'
    description = '帮助'
    usage = '.help [命令名称]'

    def declare(self) -> None:
        self.register_option('command', str, default=None, description='命令名称')


class _SendCommand(Command):
    name = 'send'
    description = '发送'
    aliases = ('mc',)

    def declare(self) -> None:
        self.register_arg('message', str, description='消息', multi=True)


class _ListCommand(Command):
    name = 'list'
    description = '列表'


class _LuckCommand(Command):
    name = 'luck'
    description = '人品'


class _ServerCommand(Command):
    name = 'server'
    description = '服务器'


def _build_all(manager: CommandManager):
    manager.validate()
    manager.build()


# ===== 收集 =====

class TestBuiltinCollection:
    def test_all_enabled_commands_registered(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        nodes = manager.get_command_nodes()
        names = {node.name for node in nodes.values()}
        assert names == {'about', 'bound', 'command', 'help', 'list', 'luck', 'send', 'server'}

    def test_command_ids_use_builtin_prefix(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        nodes = manager.get_command_nodes()
        assert all(cid.startswith('builtin:') for cid in nodes)

    def test_skips_module_without_command(self, monkeypatch):
        '''无命令类的模块应被跳过，不产生命令。'''
        manager = _make_manager(monkeypatch)
        nodes = manager.get_command_nodes()
        assert 'builtin:ai' not in nodes

    def test_register_after_build_raises(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        _build_all(manager)
        with pytest.raises(CommandError):
            manager.register_builtin_commands()


# ===== 结构 =====

class TestBuiltinStructure:
    def test_command_has_multi_argument(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:command')
        message_arg = node.find_argument('command')
        assert message_arg is not None
        assert message_arg.multi is True

    def test_send_has_alias(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:send')
        assert 'mc' in node.aliases

    def test_bound_has_four_subcommands(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:bound')
        names = {sub.name for sub in node.subcommands}
        assert names == {'list', 'query', 'remove', 'append'}

    def test_about_has_check_subcommand(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:about')
        assert node.find_subcommand('check') is not None

    def test_help_has_optional_argument(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:help')
        command_arg = node.find_argument('command')
        assert command_arg is not None
        assert command_arg.required is False

    def test_help_has_usage_and_description(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        node = manager.get_command('builtin:help')
        assert node.usage
        assert node.description

    def test_build_creates_matchers(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        _build_all(manager)
        assert len(manager._matchers) == 8