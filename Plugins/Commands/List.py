import asyncio

from nonebot.plugin import PluginMetadata

from nonebot_plugin_alconna import Command, Match
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import player_list_cache, render_template
from Scripts.Managers import cache_manager, server_manager
from Scripts.Messages import messages
from Scripts.Network import fetch_player_avatars
from Scripts.Rules import command_group_rule
from Scripts.Utils import turn_message_text

__plugin_meta__ = PluginMetadata(
    name='在线玩家',
    description='查询已连接服务器的在线玩家列表。',
    usage='.list [服务器名称]',
)

matcher = (
    Command('list <server?#服务器名称:str>', '查看服务器在线玩家列表。')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle(server: Match[str]):
    server_flag = server.result if server.available else None
    _, response = await get_players(server_flag)
    if not isinstance(response, dict):
        await matcher.finish(response)
        return
    if config.image.mode:
        player_names = {name for groups in response.values() for name in groups[0]}
        avatars = await ensure_avatars(list(player_names))
        image = await render_template('List', (600, 800), player_list=response, avatars=avatars)
        await matcher.finish(UniMessage(Image(raw=image)))
    message = await turn_message_text(list_handler(response))
    await matcher.finish(message)


async def ensure_avatars(player_names: list):
    '''获取玩家头像文件路径：本地已缓存直接复用，缺失的下载后落盘'''
    cached, missing_names = cache_manager.get_cached(player_names)
    if not missing_names:
        return cached
    contents = await fetch_player_avatars(missing_names)
    files = {cache_manager.get_path(name).name: content for name, (content, _) in contents.items()}
    saved = await cache_manager.save_all(files)
    for name in contents:
        cached[name] = saved[cache_manager.get_path(name).name]
    return cached


def split_players(players: list):
    '''将玩家列表按假人前缀分为 (真实玩家, 假人) 两组，未配置前缀时全部视为真实玩家'''
    if not config.bot_prefix:
        return list(players), []
    real_players, fake_players = [], []
    for player in players:
        if player.upper().startswith(config.bot_prefix):
            fake_players.append(player)
            continue
        real_players.append(player)
    return real_players, fake_players


async def get_players(server_flag: str | None = None):
    '''查询在线玩家列表：指定服务器查单个，否则查询全部已连接服务器'''
    if server_flag:
        server = server_manager.get_server(server_flag)
        if server is None:
            return False, messages.commands.list.server_not_found.format(server=server_flag)
        return True, {server.self_id: await query_server_players(server, server.self_id)}
    if not server_manager.servers:
        return False, messages.commands.list.no_server
    results = await asyncio.gather(
        *(query_server_players(server, name) for name, server in server_manager.servers.items())
    )
    players = dict(zip(server_manager.servers.keys(), results))
    return True, players


async def query_server_players(server, server_name: str):
    '''查询单个服务器的玩家并分组：兼容模式读取缓存，否则实时查询'''
    if config.list_compatible_mode:
        cached = player_list_cache.get(server_name, [])
        return split_players(list(cached))
    player_list, _ = await server_manager.get_player_list(server)
    return split_players(player_list)


def list_handler(players: dict):
    '''将玩家列表数据格式化为文本消息（异步生成器）'''
    if not players:
        yield messages.commands.list.no_server
        return
    if len(players) == 1:
        server_name, players_data = next(iter(players.items()))
        yield messages.commands.list.single_title.format(server=server_name)
        yield from format_players(players_data)
        total = sum(len(group) for group in players_data)
        yield messages.commands.list.player_total.format(count=total)
        return
    player_count = 0
    yield messages.commands.list.global_title
    for name, players_data in players.items():
        player_count += sum(len(group) for group in players_data)
        yield messages.commands.list.server_divider.format(name=name)
        yield from format_players(players_data)
    yield messages.commands.list.player_total.format(count=player_count)


def format_players(players: list):
    '''格式化单个服务器的玩家分组为文本'''
    real_players, fake_players = players
    if config.bot_prefix:
        yield messages.commands.list.player_section
        yield '    ' + ('\n    '.join(real_players) if real_players else messages.commands.list.no_player)
        yield messages.commands.list.fake_section
        yield '    ' + ('\n    '.join(fake_players) if fake_players else messages.commands.list.no_fake) + '\n'
        return
    if real_players:
        yield '    ' + '\n    '.join(real_players) + '\n'
        return
    yield '  ' + messages.commands.list.no_player + '\n'
