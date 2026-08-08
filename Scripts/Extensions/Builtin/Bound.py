'''内置扩展：玩家绑定指令。'''

from typing import override

from nonebot_plugin_alconna import At, Match
from nonebot_plugin_uninfo import Uninfo

from Scripts.Config import config
from .. import Command, Extension, SubCommand
from Scripts.Globals import render_template
from Scripts.Managers import data_manager, server_manager
from Scripts.Messages import messages
from Scripts.Utils import check_player, get_permission

# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(id='Bound', name='玩家绑定', version='1.0.0', types=('command',), builtin=True)


@extension.register_command
class BoundCommand(Command):
    '''管理玩家白名单绑定。'''

    name = 'bound'
    description = '管理玩家白名单绑定。'
    usage = '.bound [玩家名|子命令]'

    class List(SubCommand['BoundCommand']):
        '''列出所有绑定。'''

        name = 'list'
        description = '列出所有绑定'

        @override
        @override
        async def handler(self, session: Uninfo):
            if not get_permission(session):
                return messages.commands.bound.no_permission
            if not data_manager.players:
                return messages.commands.bound.no_binding
            return messages.commands.bound.list_title + '\n' + '\n'.join(
                f'  {user} -> {'、'.join(players)}' for user, players in data_manager.players.items()
            )

        @override
        async def image_handler(self, session: Uninfo) -> bytes | None:
            '''渲染绑定列表为图片，返回 PNG 字节（由框架在图像模式发送）。'''
            if not get_permission(session):
                return messages.commands.bound.no_permission
            if not data_manager.players:
                return messages.commands.bound.no_binding
            bindings = [
                {'user': user, 'players': players}
                for user, players in data_manager.players.items()
            ]
            return await render_template('Bound', (600, 800), bindings=bindings)

    class Query(SubCommand['BoundCommand']):
        '''查询指定用户的绑定。'''

        name = 'query'
        description = '查询指定用户的绑定'

        @override
        def declare(self) -> None:
            self.register_option('user_id', At | str, default=None, description='用户')

        @override
        async def handler(self, session: Uninfo, user_id: Match[At | str]):
            target_user = user_id.result if user_id.available else str(session.user.id)
            if isinstance(target_user, At):
                target_user = target_user.target
            if target_user not in data_manager.players:
                return messages.commands.bound.not_bound_query.format(target_user=target_user)
            players = '、'.join(data_manager.players[target_user])
            return messages.commands.bound.query_result.format(target_user=target_user, players=players)

    class Remove(SubCommand['BoundCommand']):
        '''移除指定绑定。'''

        name = 'remove'
        description = '移除指定绑定'

        @override
        def declare(self) -> None:
            self.register_option('player', At | str, default=None, description='玩家')

        @override
        async def handler(self, session: Uninfo, player: Match[str]):
            current_user = str(session.user.id)
            if not player.available:
                # .bound remove - 自己解绑全部
                return await self.parent.bound_remove_self_all(session)
            # .bound remove <QQ> - 管理员解绑用户
            if player.result != current_user and not get_permission(session):
                return messages.commands.bound.no_permission
            return await self.parent.bound_remove_user(player.result)

    class Append(SubCommand['BoundCommand']):
        '''为指定用户添加绑定。'''

        name = 'append'
        description = '为指定用户添加绑定'

        @override
        def declare(self) -> None:
            self.register_arg('user_id', At | str, description='用户')
            self.register_arg('player', str, description='玩家')

        @override
        async def handler(self, session: Uninfo, user_id: At | str, player: str):
            if not get_permission(session):
                return messages.commands.bound.no_permission
            return await self.parent.bound_append_handler(
                user_id.target if isinstance(user_id, At) else user_id, player
            )

    @override
    def declare(self) -> None:
        self.register_option('player', str, default=None, description='要绑定的玩家名')

    @override
    async def handler(self, session: Uninfo, player: Match[str]):
        '''处理 .bound <player>'''
        if not player.available:
            return messages.commands.bound.invalid_name
        return await self.bound_handler(session, player.result)

    async def bound_handler(self, session: Uninfo, player: str):
        if not check_player(player):
            return messages.commands.bound.invalid_name
        user = str(session.user.id)
        if user in data_manager.players and player in data_manager.players[user]:
            return messages.commands.bound.already_bound
        if await data_manager.check_player_occupied(player):
            return messages.commands.bound.occupied
        if not server_manager.check_online():
            return messages.commands.bound.server_offline
        if await data_manager.append_player(user, player):
            await server_manager.execute(f'{config.whitelist_command} add {player}')
            return messages.commands.bound.bound_success.format(name=session.user.name or user, user=user, player=player)
        return messages.commands.bound.too_many

    async def bound_append_handler(self, target_user: str, player: str):
        '''为指定用户添加玩家绑定（Append 子命令）。'''
        if not check_player(player):
            return messages.commands.bound.invalid_name
        if await data_manager.check_player_occupied(player):
            return messages.commands.bound.occupied
        if not server_manager.check_online():
            return messages.commands.bound.server_offline
        if await data_manager.append_player(target_user, player):
            await server_manager.execute(f'{config.whitelist_command} add {player}')
            return messages.commands.bound.bound_success.format(
                name=target_user, user=target_user, player=player
            )
        return messages.commands.bound.too_many

    async def bound_remove_user(self, target_user: str):
        if not server_manager.check_online():
            return messages.commands.bound.server_offline_try
        bounded = await data_manager.remove_player(target_user)
        if not bounded:
            return messages.commands.bound.not_bound_query.format(target_user=target_user)
        for player in bounded:
            await server_manager.execute(f'{config.whitelist_command} remove {player}')
        return messages.commands.bound.remove_user_all.format(target_user=target_user)

    async def bound_remove_self_all(self, session: Uninfo):
        if not server_manager.check_online():
            return messages.commands.bound.server_offline_try
        user = str(session.user.id)
        bounded = await data_manager.remove_player(user)
        if not bounded:
            return messages.commands.bound.no_binding_self
        for player in bounded:
            await server_manager.execute(f'{config.whitelist_command} remove {player}')
        return messages.commands.bound.remove_self_all