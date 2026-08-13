import asyncio
import re
from collections.abc import AsyncIterable, Iterable

from nonebot_plugin_alconna import SupportScope as AlconnaSupportScope
from nonebot_plugin_alconna import Target
from nonebot_plugin_uninfo import SupportScope as UninfoSupportScope

from Scripts.Logging import logger

from .Config import config

regex = re.compile(r'[A-Z0-9_]+|\.[A-Z0-9_]+', re.IGNORECASE)
scope_mapping = {
    str(UninfoSupportScope.qq_client): 'QQ',
    str(UninfoSupportScope.qq_api): 'QQ',
    str(UninfoSupportScope.qq_guild): 'QQ',
    str(UninfoSupportScope.telegram): 'Telegram',
    str(UninfoSupportScope.discord): 'Discord',
    str(UninfoSupportScope.dodo): 'DoDo',
    str(UninfoSupportScope.kook): 'Kook',
    str(UninfoSupportScope.wechat): 'WX',
    str(UninfoSupportScope.wecom): 'WX',
}


async def turn_message_text(iterator: AsyncIterable[str] | Iterable[str]) -> str:
    if isinstance(iterator, Iterable):
        return '\n'.join(iterator)
    return '\n'.join([text async for text in iterator])


def check_player(player: str) -> bool:
    return len(player) <= 16 and get_player_name(player) == player


def check_message(message: str) -> bool:
    return any(word in message for word in config.sync_sensitive_words)


def get_player_name(name: str) -> str | None:
    if result := regex.search(name):
        return result.group()


def get_platform_name(scope: str) -> str:
    """获取平台的可读名称。"""
    return scope_mapping.get(scope, '未知平台')


async def send_message_to_groups(message: str) -> bool:
    """向配置中的所有平台群组发送消息。"""
    send_tasks = []
    try:
        for group_info in config.message_groups:
            platform, separator, group_id = group_info.partition(':')
            if not separator or not group_id:
                logger.warning(f'消息群配置格式错误：{group_info}！')
                continue
            scope = getattr(AlconnaSupportScope, platform.lower(), None)
            if scope is None:
                logger.warning(f'不支持的平台类型：{platform}，请检查配置文件！')
                continue
            send_tasks.append(Target.group(group_id, scope).send(message))
        if send_tasks:
            await asyncio.gather(*send_tasks)
        return True
    except Exception as error:
        logger.warning(f'发送群消息失败：{error}')
        return False


def get_permission(session) -> bool:
    """检查用户是否为超级用户或管理员。"""
    uid = str(session.user.id)
    if uid in config.superusers:
        return True
    if config.admin_superusers and session.member and session.member.role:
        return session.member.role.id in ('OWNER', 'ADMINISTRATOR')
    return False
