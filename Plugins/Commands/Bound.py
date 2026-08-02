from nonebot.plugin import PluginMetadata

from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import At, Command, Match
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers import data_manager, server_manager
from Scripts.Messages import messages
from Scripts.Utils import check_player, get_permission
from Scripts.Rules import command_group_rule

__plugin_meta__ = PluginMetadata(
    name='玩家绑定',
    description='管理聊天用户与 Minecraft 玩家及白名单的绑定关系。',
    usage='.bound [玩家名|子命令]',
)

matcher = (
    Command('bound <player?#要绑定的玩家名:str>', '管理玩家白名单绑定。')
    .subcommand('list #列出所有绑定')
    .subcommand('query <user_id?:At|str> #查询指定用户的绑定')
    .subcommand('remove <player:At|str> #移除指定绑定')
    .subcommand('append <user_id:At|str> <player:str> #为指定用户添加绑定')
    .build(rule=command_group_rule, use_cmd_start=True)
)

@matcher.assign('$main')
async def handle_base(session: Uninfo, player: Match[str]):
    '''处理 .bound <player>'''
    if not player.available:
        await matcher.finish(messages.commands.bound.invalid_name)
    message = await bound_handler(session, player.result)
    await matcher.finish(message)


async def bound_handler(session: Uninfo, player: str):
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


@matcher.assign('list')
async def handle_list(session: Uninfo):
    '''处理 .bound list'''
    if not get_permission(session):
        await matcher.finish(messages.commands.bound.no_permission)
    if not data_manager.players:
        await matcher.finish(messages.commands.bound.no_binding)
    if config.image.mode:
        bindings = [
            {'user': user, 'players': players}
            for user, players in data_manager.players.items()
        ]
        image = await render_template('Bound', (600, 800), bindings=bindings)
        await matcher.finish(UniMessage(Image(raw=image)))
    message = messages.commands.bound.list_title + '\n' + '\n'.join(
        f'  {user} -> {'、'.join(players)}' for user, players in data_manager.players.items()
    )
    await matcher.finish(message)


@matcher.assign('query')
async def handle_query(session: Uninfo, user_id: Match[At | str]):
    '''处理 .bound query [user_id]'''
    target_user = user_id.result if user_id.available else str(session.user.id)
    if isinstance(target_user, At):
        target_user = target_user.target
    if target_user not in data_manager.players:
        await matcher.finish(messages.commands.bound.not_bound_query.format(target_user=target_user))
    players = '、'.join(data_manager.players[target_user])
    await matcher.finish(messages.commands.bound.query_result.format(target_user=target_user, players=players))


@matcher.assign('remove')
async def handle_remove(session: Uninfo, player: Match[str]):
    '''处理 .bound remove [player]'''
    current_user = str(session.user.id)
    if not player.available:
        # .bound remove - 自己解绑全部
        await matcher.finish(await bound_remove_self_all(session))
    # .bound remove <QQ> - 管理员解绑用户
    if player.result != current_user and not get_permission(session):
        await matcher.finish(messages.commands.bound.no_permission)
    await matcher.finish(await bound_remove_user(player.result))


@matcher.assign('append')
async def handle_append(session: Uninfo, user_id: At | str, player: str):
    '''处理 .bound append <user_id> <player>'''
    if not get_permission(session):
        await matcher.finish(messages.commands.bound.no_permission)
    message = await bound_append_handler(user_id.target if isinstance(user_id, At) else user_id, player)
    await matcher.finish(message)


async def bound_append_handler(user: str, player: str):
    if not check_player(player):
        return messages.commands.bound.invalid_name_short
    if await data_manager.check_player_occupied(player):
        return messages.commands.bound.occupied
    if not server_manager.check_online():
        return messages.commands.bound.server_offline_try
    if await data_manager.append_player(user, player):
        await server_manager.execute(f'{config.whitelist_command} add {player}')
        return messages.commands.bound.bound_success.format(name=user, user=user, player=player)
    return messages.commands.bound.too_many


async def bound_remove_player(session: Uninfo, player_name: str):
    if not server_manager.check_online():
        return messages.commands.bound.server_offline_try
    user = str(session.user.id)
    if await data_manager.remove_player(user, player_name):
        await server_manager.execute(f'{config.whitelist_command} remove {player_name}')
        return messages.commands.bound.remove_success.format(player_name=player_name)
    return messages.commands.bound.no_such_whitelist.format(player_name=player_name)


async def bound_remove_user(target_user: str):
    if not server_manager.check_online():
        return messages.commands.bound.server_offline_try
    bounded = await data_manager.remove_player(target_user)
    if not bounded:
        return messages.commands.bound.not_bound_query.format(target_user=target_user)
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return messages.commands.bound.remove_user_all.format(target_user=target_user)


async def bound_remove_self_all(session: Uninfo):
    if not server_manager.check_online():
        return messages.commands.bound.server_offline_try
    user = str(session.user.id)
    bounded = await data_manager.remove_player(user)
    if not bounded:
        return messages.commands.bound.no_binding_self
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return messages.commands.bound.remove_self_all
