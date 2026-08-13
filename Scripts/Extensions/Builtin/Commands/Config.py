"""内置扩展：配置管理指令。"""

from typing import override

from nonebot_plugin_alconna import At
from nonebot_plugin_uninfo import SupportScope, Uninfo

from Scripts.Config import config
from Scripts.Extensions import Command, Extension, SubCommand
from Scripts.Logging import logger
from Scripts.Managers import config_manager
from Scripts.Messages import messages
from Scripts.Utils import get_permission

# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(id='Config', name='配置管理', version='1.0.0', types=('command',))

# 配置项别名 → 规范字段名（message_groups / command_groups 支持简称）
_CONFIG_FIELDS = {
    'message_groups': 'message_groups',
    'msg_grps': 'message_groups',
    'command_groups': 'command_groups',
    'cmd_grps': 'command_groups',
    'superusers': 'superusers',
}


@extension.register_command
class ConfigCommand(Command):
    """管理机器人配置（消息群 / 指令群 / 超级用户）。"""

    name = 'config'
    description = '管理机器人配置。'
    usage = '/config add|remove <目标> <配置项>'

    class Add(SubCommand['ConfigCommand']):
        """添加配置项。"""

        name = 'add'
        description = '添加配置项'

        @override
        def declare(self) -> None:
            self.register_arg('target', At | str, description='目标（. 当前群聊 / @用户 / 用户ID）')
            self.register_arg('item', str, description='配置项名称')

        @override
        async def handler(self, session: Uninfo, target: At | str, item: str):
            if not get_permission(session):
                return messages.commands.config.no_permission
            return await self.parent.update_config(session, target, item, remove=False)

    class Remove(SubCommand['ConfigCommand']):
        """移除配置项。"""

        name = 'remove'
        description = '移除配置项'

        @override
        def declare(self) -> None:
            self.register_arg('target', At | str, description='目标（. 当前群聊 / @用户 / 用户ID）')
            self.register_arg('item', str, description='配置项名称')

        @override
        async def handler(self, session: Uninfo, target: At | str, item: str):
            if not get_permission(session):
                return messages.commands.config.no_permission
            return await self.parent.update_config(session, target, item, remove=True)

    async def update_config(self, session: Uninfo, target: At | str, item: str, remove: bool) -> str:
        """按目标与配置项执行增删，返回操作结果消息。"""
        field_name = _CONFIG_FIELDS.get(item.lower())
        if field_name is None:
            return messages.commands.config.unknown_config.format(name=item)
        if field_name == 'superusers':
            if isinstance(target, At):
                return self.update_superusers(str(target.target), remove)
            if target == '.':
                return messages.commands.config.user_only.format(name=item)
            return self.update_superusers(str(target), remove)
        if isinstance(target, At):
            return messages.commands.config.group_only.format(name=item)
        if target == '.':
            group_id = session.scene.id
            if not group_id:
                return messages.commands.config.no_scene
            return self.update_groups(field_name, f'{SupportScope(session.scope).name}:{group_id}', remove)
        return self.update_groups(field_name, str(target), remove)

    def update_superusers(self, user_id: str, remove: bool) -> str:
        """增删超级用户：写回 .env 持久化并热更新内存。"""
        current = list(config.superusers)
        if remove:
            if user_id not in current:
                return messages.commands.config.not_found.format(value=user_id, name='superusers')
            current.remove(user_id)
        else:
            if user_id in current:
                return messages.commands.config.already_added.format(value=user_id, name='superusers')
            current.append(user_id)
        try:
            config_manager.update_env({'SUPERUSERS': current})
        except Exception as error:
            logger.warning(f'写入 .env 失败：{error}')
            return messages.commands.config.write_failed
        # 热更新内存，使本项目权限检查立即生效（框架权限需重启后完全生效）
        config.superusers = current
        action = messages.commands.config.remove_success if remove else messages.commands.config.add_success
        return action.format(value=user_id, name='superusers') + messages.commands.config.restart_hint

    def update_groups(self, field_name: str, value: str, remove: bool) -> str:
        """增删消息群 / 指令群：写回 Config.toml 并热更新内存。"""
        current = list(getattr(config, field_name))
        if remove:
            if value not in current:
                return messages.commands.config.not_found.format(value=value, name=field_name)
            current.remove(value)
        else:
            if value in current:
                return messages.commands.config.already_added.format(value=value, name=field_name)
            current.append(value)
        try:
            config_manager.update_config({field_name: current})
        except Exception as error:
            logger.warning(f'写入 Config.toml 失败：{error}')
            return messages.commands.config.write_failed
        # 热更新内存（不调 reload_config，避免以启动时的 .env 值覆盖 superusers 等字段）
        setattr(config, field_name, current)
        action = messages.commands.config.remove_success if remove else messages.commands.config.add_success
        return action.format(value=value, name=field_name)
