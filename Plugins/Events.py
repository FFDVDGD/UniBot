import asyncio
from datetime import datetime

from nonebot import on_notice, on_message
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters.minecraft import PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent, PlayerDeathEvent
from nonebot.adapters.minecraft.message import MessageSegment
from nonebot.adapters.minecraft.models import HoverAction, HoverEvent, Component

from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna.uniseg import UniMsg

from Scripts.Config import config
from Scripts.Globals import player_list_cache
from Scripts.Managers import server_manager
from Scripts.Utils import check_message, get_platform_name, send_message_to_groups
from Scripts.Rules import message_group_rule

__plugin_meta__ = PluginMetadata(
    name='消息互通事件',
    description='处理玩家事件以及聊天平台与 Minecraft 服务器之间的消息同步。',
    usage='由相关消息与服务器事件自动触发。',
)

notice_watcher = on_notice()
player_chat_watcher = on_message()
message_watcher = on_message(rule=message_group_rule)


segment_mapping = {
    'text': lambda seg: seg.text,
    'at': lambda seg: f'[@{seg.target}]',
    'reply': lambda seg: f'[引用{"：" + seg.msg.extract_plain_text() if seg.msg else ""}]',
    'reference': lambda seg: '[引用消息]',
    'atall': lambda seg: '[@全体成员]',
    'emoji': lambda seg: '[动画表情]',
    'image': lambda seg: '[图片]',
    'video': lambda seg: '[视频]',
    'audio': lambda seg: '[语音]',
    'file': lambda seg: '[文件]'
}


def message_to_text(message: UniMsg):
    '''将 UniMsg 转换为文本'''

    texts = [func(seg) for seg in message if (func := segment_mapping.get(seg.type)) is not None if func(seg)]
    return ' '.join(texts)


def build_server_message(source: str, player: str, content: str):
    '''构建服务器消息'''
    now_time = datetime.now().strftime('%H:%M:%S')
    hover_event = HoverEvent(action=HoverAction.show_text, contents=Component(text=now_time))
    message = MessageSegment.text(f'[{source}] ', color=config.sync_color_source, hover_event=hover_event)
    message += MessageSegment.text(f'[{player}] ', color=config.sync_color_player, hover_event=hover_event)
    message += MessageSegment.text(content, color=config.sync_color_message, hover_event=hover_event)
    return message


@notice_watcher.handle()
async def handle_player_join(event: PlayerJoinEvent):
    '''处理玩家加入服务器事件'''
    name = event.server_name
    player = event.player.nickname
    logger.info(f'收到玩家 {player} 加入服务器 [{name}] 通知！')

    if config.list_compatible_mode:
        if name not in player_list_cache:
            player_list_cache[name] = []
        if not config.bot_prefix or not player.upper().startswith(config.bot_prefix):
            if player not in player_list_cache[name]:
                player_list_cache[name].append(player)

    server_message = f'玩家 {player} 加入了游戏。'
    group_message = f'玩家 {player} 加入了 [{name}] 服务器，喵～'

    if config.bot_prefix and player.upper().startswith(config.bot_prefix):
        group_message = f'机器人 {player} 加入了 [{name}] 服务器。'
        server_message = f'[{name}] 机器人 {player} 加入了游戏。'

    if config.sync_message_between_servers:
        await server_manager.broadcast(build_server_message(name, player, server_message), name)

    if config.broadcast_player:
        await send_message_to_groups(group_message)


@notice_watcher.handle()
async def handle_player_quit(event: PlayerQuitEvent):
    '''处理玩家离开服务器事件'''
    name = event.server_name
    player = event.player.nickname
    logger.info(f'收到玩家 {player} 离开服务器 [{name}] 通知！')

    if config.list_compatible_mode:
        if name in player_list_cache and player in player_list_cache[name]:
            player_list_cache[name].remove(player)

    server_message = f'玩家 {player} 离开了游戏。'
    group_message = f'玩家 {player} 离开了 [{name}] 服务器，呜……'

    if config.bot_prefix and player.upper().startswith(config.bot_prefix):
        server_message = f'机器人 {player} 离开了游戏。'
        group_message = f'机器人 {player} 离开了 [{name}] 服务器。'

    if config.sync_message_between_servers:
        await server_manager.broadcast(build_server_message(name, player, server_message), name)

    if config.broadcast_player:
        await send_message_to_groups(group_message)


@notice_watcher.handle()
async def handle_player_death(event: PlayerDeathEvent):
    '''处理玩家死亡事件'''
    name = event.server_name
    player = event.player.nickname
    death_message = event.death.text or f'{player} 死亡了'
    logger.debug(f'收到玩家死亡消息：{death_message}')

    if (not config.bot_prefix) or (not player.upper().startswith(config.bot_prefix)):
        broadcast_message = f'玩家 {player} 死亡了，呜……'
        if config.sync_message_between_servers:
            await server_manager.broadcast(build_server_message(name, player, broadcast_message), name)
        if config.broadcast_player:
            await send_message_to_groups(broadcast_message)


@player_chat_watcher.handle()
async def handle_player_chat(event: PlayerChatEvent):
    '''处理玩家聊天事件'''
    name = event.server_name
    player = event.player.nickname
    chat_message = event.message.extract_plain_text().strip()
    logger.debug(f'收到玩家 {player} 在服务器 [{name}] 发送消息！')

    if config.sync_message_between_servers:
        asyncio.create_task(server_manager.broadcast(build_server_message(name, player, chat_message), name))

    if config.sync_all_game_message:
        if check_message(chat_message):
            logger.warning(f'检测到消息 {chat_message} 包含敏感词，已丢弃！')
            await send_message_to_groups(f'检测到玩家 {player} 发送的消息包含敏感词，已丢弃！详情请看控制台。')
            await player_chat_watcher.finish()

        await send_message_to_groups(f'[{name}] <{player}> {chat_message}')
        await player_chat_watcher.finish()

    logger.debug(f'收到服务器消息：{chat_message}')
    old_message = chat_message
    for command in ('send', 'gp', 'qq', 'q'):
        if chat_message.startswith(command):
            chat_message = chat_message.lstrip(command).strip()
    if old_message == chat_message:
        await player_chat_watcher.finish()
    if not chat_message:
        message = MessageSegment.text('请在指令后输入要发送的消息！', color='red')
        await player_chat_watcher.finish(message)
    if check_message(chat_message):
        message = MessageSegment.text('检测到消息包含敏感词，已丢弃！', color='red')
        await player_chat_watcher.finish(message)
    await send_message_to_groups(f'[{name}] <{player}> {chat_message}')
    message = MessageSegment.text('消息已发送！', color='green')
    await player_chat_watcher.finish(message)


@message_watcher.handle()
async def handle_group_message(message: UniMsg, session: Uninfo):
    platform_name = get_platform_name(session.scope)
    plain_text_message = message.extract_plain_text()
    if any(plain_text_message.startswith(prefix) for prefix in config.command_start):
        await message_watcher.finish()
    user_name = session.user.nick or session.user.name or str(session.user.id)
    await server_manager.broadcast(build_server_message(platform_name, user_name, message_to_text(message)))
