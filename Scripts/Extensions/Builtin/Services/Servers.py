"""内置服务：Minecraft 服务器交互。"""

import asyncio
import re
from typing import override

from nonebot import get_adapter
from nonebot.adapters.minecraft import Adapter as MCAdapter
from nonebot.adapters.minecraft import Bot
from nonebot.adapters.minecraft.message import Message
from nonebot.log import logger

from Scripts import Globals
from Scripts.Extensions import Extension, Service

extension = Extension(id='Servers', name='Minecraft 服务器服务', version='1.0.0', types=('api',))


@extension.register_service
class ServerService(Service):
    """封装 Minecraft 服务器查询、指令执行与消息广播能力。"""

    name = 'server'

    def __init__(self) -> None:
        self.servers: dict[str, Bot] = {}

    @override
    async def on_enable(self) -> None:
        """服务启动时绑定 Minecraft 适配器的机器人集合。"""
        adapter = get_adapter(MCAdapter)
        self.servers = adapter.bots  # pyright: ignore[reportAttributeAccessIssue]
        Globals.server_service = self

    @override
    async def on_disable(self) -> None:
        """服务关闭时释放适配器机器人集合引用。"""
        if Globals.server_service is self:
            Globals.server_service = None
        self.servers = {}

    def get_server(self, server_flag: str | int) -> Bot | None:
        """通过名称或编号获取 Minecraft 机器人。"""
        if isinstance(server_flag, int) or server_flag.isdigit():
            names = list(self.servers.keys())
            index = int(server_flag) - 1
            if 0 <= index < len(names):
                return self.servers[names[index]]
        return self.servers.get(str(server_flag))

    def check_online(self) -> bool:
        """是否有 Minecraft 服务器在线。"""
        return bool(self.servers)

    async def gather(self, get_task, filter_function=None):
        """并发调用所有符合条件的 Minecraft 服务器。"""
        names: list[str] = []
        tasks = []
        for name, server in self.servers.items():
            if filter_function is None or filter_function(server):
                names.append(name)
                tasks.append(get_task(server))
        results = await asyncio.gather(*tasks)
        return {names[index]: result for index, result in enumerate(results)}

    async def execute(self, command: str, server_flag: str | int | None = None):
        """执行 Minecraft 指令，server_flag 为 None 时广播到所有服务器。"""

        async def get_task(server: Bot):
            try:
                return await server.send_rcon_command(command=command)
            except Exception as error:
                logger.warning(f'向服务器 [{server.self_id}] 发送指令失败：{error}')

        if server_flag is not None:
            bot = self.get_server(server_flag)
            if bot is not None:
                return {bot.self_id: await bot.send_rcon_command(command=command)}
            return None
        return await self.gather(get_task)

    async def get_status(self, server: Bot) -> dict:
        """获取 Minecraft 服务器状态。"""
        try:
            status = await server.get_status()
        except Exception as error:
            logger.warning(f'获取服务器 [{server.self_id}] 状态失败：{error}')
            return {
                'online': False,
                'server_type': '',
                'players': 0,
                'max_players': 0,
                'version': '',
                'motd': '',
                'cpu_load': 0.0,
                'memory_percent': 0.0,
                'jvm_memory_used': 0,
                'jvm_memory_max': 0,
            }

        server_ping = status.server_list_ping
        player_status = server_ping.players
        version_status = server_ping.version
        cpu_info = status.cpu_information
        jvm_memory = status.memory_information.jvm_memory

        return {
            'online': server_ping.available,
            'server_type': status.server_type,
            'players': int(player_status.online) if player_status else 0,
            'max_players': int(player_status.max) if player_status else 0,
            'version': version_status.name if version_status else status.server_version,
            'motd': server_ping.description,
            'cpu_load': round(max(cpu_info.system_load, cpu_info.process_load), 1),
            'memory_percent': round(jvm_memory.percentage, 1),
            'jvm_memory_used': round(jvm_memory.used / 1024 / 1024, 1),
            'jvm_memory_max': round(jvm_memory.max / 1024 / 1024, 1),
        }

    async def get_player_list(self, server: Bot) -> tuple[list[str], int]:
        """通过 RCON 指令获取并解析服务器玩家列表。"""
        try:
            result = await server.send_rcon_command(command='list')
        except Exception as error:
            logger.warning(f'获取服务器 [{server.self_id}] 玩家列表失败：{error}')
            return [], 0
        if not result:
            return [], 0

        match = re.search(r'^There are \d+ of (?:a )?max(?: of)? (\d+) players online:\s*(.*)$', result.strip())
        if match is None:
            logger.warning(f'解析服务器 [{server.self_id}] 玩家列表失败：{result}')
            return [], 0
        max_players = int(match.group(1))
        players = [player.strip() for player in match.group(2).split(',') if player.strip()]
        return players, max_players

    async def broadcast(self, message: Message | str, except_server: str = ''):
        """广播消息到所有服务器（除 except_server 外）。"""

        async def get_task(server: Bot):
            try:
                return await server.send_msg(message=message)
            except Exception as error:
                logger.warning(f'向服务器 [{server.self_id}] 广播消息失败：{error}')

        return await self.gather(get_task, lambda server: server.self_id != except_server)
