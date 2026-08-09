"""
内置指令重构测试：单文件扩展经 Loader 加载产生 builtin: 前缀（验证点 3、4、11）。

真实内置扩展（Extensions/*.py）依赖 config/Globals/Managers/Messages 等运行时模块，
测试不直接导入，改用轻量假命令类 + 假扩展实例，验证 Loader._commit_commands 的
内置命令前缀逻辑与 CommandManager 结构。
"""

from typing import override

import pytest

from Scripts.Extensions import Command, CommandError, CommandManager, SubCommand, command_manager
from Scripts.Extensions.Loader import ExtensionLoader


def _make_extension(command_cls: type) -> 'object':
    """构造一个声明了单个命令类的假扩展实例。"""
    from Scripts.Extensions import Extension

    extension = Extension()
    extension.commands = [command_cls]
    return extension


def _commit(commands: dict[str, 'object'], builtin: bool = True):
    """
    用假扩展实例驱动 Loader._commit_commands，模拟扩展声明阶段。

        Loader 将命令注册到全局 command_manager 单例（conftest 已按测试清空）。
    """
    loader = ExtensionLoader(command_manager)
    for extension_id, extension in commands.items():
        loader._commit_commands(extension_id, extension, builtin=builtin)
    return command_manager


def _build_all(manager: CommandManager):
    manager.validate()
    manager.build()


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

    @override
    def declare(self) -> None:
        self.register_arg('server', str, description='服务器')
        self.register_arg('command', str, description='命令', multi=True)


class _HelpCommand(Command):
    name = 'help'
    description = '帮助'
    usage = '.help [命令名称]'

    @override
    def declare(self) -> None:
        self.register_option('command', str, default=None, description='命令名称')


class _SendCommand(Command):
    name = 'send'
    description = '发送'
    aliases = ('mc',)

    @override
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
    def test_all_enabled_commands_registered(self):
        manager = _commit(
            {
                'About': _make_extension(_AboutCommand),
                'Bound': _make_extension(_BoundCommand),
                'Command': _make_extension(_ConsoleCommand),
                'Help': _make_extension(_HelpCommand),
                'List': _make_extension(_ListCommand),
                'Luck': _make_extension(_LuckCommand),
                'Send': _make_extension(_SendCommand),
                'Server': _make_extension(_ServerCommand),
            }
        )
        nodes = manager.get_command_nodes()
        names = {node.name for node in nodes.values()}
        assert names == {'about', 'bound', 'command', 'help', 'list', 'luck', 'send', 'server'}

    def test_command_ids_use_builtin_prefix(self):
        manager = _commit({'Send': _make_extension(_SendCommand)})
        nodes = manager.get_command_nodes()
        assert all(cid.startswith('builtin:') for cid in nodes)

    def test_extension_prefix_used_for_non_builtin(self):
        """非内置扩展命令使用 extension: 前缀。"""

        extension = _make_extension(_SendCommand)
        manager = _commit({'WeatherExt': extension}, builtin=False)
        assert 'extension:WeatherExt:send' in manager.get_command_nodes()

    def test_register_after_build_raises(self):
        manager = _commit({'Send': _make_extension(_SendCommand)})
        _build_all(manager)
        with pytest.raises(CommandError):
            manager.register_command(_SendCommand(), 'builtin:send')


# ===== 结构 =====


class TestBuiltinStructure:
    def test_command_has_multi_argument(self):
        manager = _commit({'Command': _make_extension(_ConsoleCommand)})
        node = manager.get_command('builtin:command')
        message_arg = node.find_argument('command')
        assert message_arg is not None
        assert message_arg.multi is True

    def test_send_has_alias(self):
        manager = _commit({'Send': _make_extension(_SendCommand)})
        node = manager.get_command('builtin:send')
        assert 'mc' in node.aliases

    def test_bound_has_four_subcommands(self):
        manager = _commit({'Bound': _make_extension(_BoundCommand)})
        node = manager.get_command('builtin:bound')
        names = {sub.name for sub in node.subcommands}
        assert names == {'list', 'query', 'remove', 'append'}

    def test_about_has_check_subcommand(self):
        manager = _commit({'About': _make_extension(_AboutCommand)})
        node = manager.get_command('builtin:about')
        assert node.find_subcommand('check') is not None

    def test_help_has_optional_argument(self):
        manager = _commit({'Help': _make_extension(_HelpCommand)})
        node = manager.get_command('builtin:help')
        command_arg = node.find_argument('command')
        assert command_arg is not None
        assert command_arg.required is False

    def test_help_has_usage_and_description(self):
        manager = _commit({'Help': _make_extension(_HelpCommand)})
        node = manager.get_command('builtin:help')
        assert node.usage
        assert node.description

    def test_build_creates_matchers(self):
        manager = _commit(
            {
                'About': _make_extension(_AboutCommand),
                'Bound': _make_extension(_BoundCommand),
                'Command': _make_extension(_ConsoleCommand),
                'Help': _make_extension(_HelpCommand),
                'List': _make_extension(_ListCommand),
                'Luck': _make_extension(_LuckCommand),
                'Send': _make_extension(_SendCommand),
                'Server': _make_extension(_ServerCommand),
            }
        )
        _build_all(manager)
        assert len(manager._matchers) == 8


# ===== 单文件清单构建 =====


class TestManifestFromAttributes:
    def test_builds_manifest_from_class_attributes(self):
        from Scripts.Extensions import Extension, ExtensionType, manifest_from_attributes

        class FakeExt(Extension):
            id = 'Fake'
            name = '假扩展'
            version = '1.0.0'
            types = ('command',)

        manifest = manifest_from_attributes(FakeExt())
        assert manifest.extension.id == 'Fake'
        assert manifest.extension.name == '假扩展'
        assert manifest.extension.types == [ExtensionType('command')]

    def test_builds_manifest_from_constructor_kwargs(self):
        """直接实例化 Extension 并传入元数据参数，无需继承。"""
        from Scripts.Extensions import Extension, ExtensionType, manifest_from_attributes

        extension = Extension(id='Fake', name='假扩展', version='1.0.0', types=('command',))
        manifest = manifest_from_attributes(extension)
        assert manifest.extension.id == 'Fake'
        assert manifest.extension.name == '假扩展'
        assert manifest.extension.types == [ExtensionType('command')]

    def test_missing_id_raises(self):
        from Scripts.Extensions import Extension, ManifestError, manifest_from_attributes

        class FakeExt(Extension):
            name = '假扩展'
            version = '1.0.0'

        with pytest.raises(ManifestError):
            manifest_from_attributes(FakeExt())

    def test_constructor_without_id_raises(self):
        from Scripts.Extensions import Extension, ManifestError, manifest_from_attributes

        extension = Extension(name='假扩展', version='1.0.0')
        with pytest.raises(ManifestError):
            manifest_from_attributes(extension)
