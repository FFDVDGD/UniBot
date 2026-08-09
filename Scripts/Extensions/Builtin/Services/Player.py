'''内置服务：玩家绑定数据管理。

把玩家绑定数据从 DataManager 抽取为内置 API 服务，供内置命令、事件处理器与
WebUI API 通过 `extension.api.get(PlayerService)`（或全局注册名 `player`）获取。
数据经内置扩展的目录式存储直接落盘为 `Data/Player.json`。
'''

from typing import cast, override

from Scripts.Config import config
from Scripts.Extensions import Extension, ExtensionDataStore, Service

# 创建唯一扩展实例，能力经实例装饰器登记
# 内置扩展数据存储指向 Data 根目录，Player 扩展读写 `Player.json`
extension = Extension(id='PlayerService', name='玩家绑定服务', version='1.0.0', types=('api', ))

# 玩家绑定数据文件名（位于 Data 根目录）
DATA_FILE = 'Players.json'


@extension.register_service
class PlayerService(Service):
    '''管理用户与游戏 ID 的绑定关系，数据同源落盘 `Data/Player.json`。'''
    @property
    def players(self) -> dict[str, list[str]]:
        '''读取全部绑定关系：{user_id: [player, ...]}。'''
        store = cast(ExtensionDataStore, extension.data)
        return store.read_json(DATA_FILE) or {}

    @override
    async def on_enable(self) -> None:
        '''服务启动时校验数据文件可读写，确保后续绑定操作可用。'''
        store = cast(ExtensionDataStore, extension.data)
        store.read_json(DATA_FILE)

    @override
    async def on_disable(self) -> None:
        '''服务关闭时无需额外清理，数据已实时落盘。'''

    async def append_player(self, user: str, player: str) -> bool:
        '''为用户追加一个玩家绑定，受绑定数量上限约束。'''

        store = cast(ExtensionDataStore, extension.data)
        players = dict(store.read_json(DATA_FILE) or {})
        bounded = players.get(user, [])
        if config.qq_bound_max_number > 0 and len(bounded) >= config.qq_bound_max_number:
            return False
        players[user] = [*bounded, player]
        store.write_json(DATA_FILE, players)
        return True

    async def remove_player(self, user: str, player: str = '') -> list[str]:
        '''移除用户绑定；player 为空时移除全部，返回被移除的玩家列表（空列表表示无绑定）。'''
        store = cast(ExtensionDataStore, extension.data)
        players = dict(store.read_json(DATA_FILE) or {})
        bounded = players.get(user, [])
        if player:
            if player not in bounded:
                return []
            remaining = [p for p in bounded if p != player]
            if remaining:
                players[user] = remaining
            else:
                players.pop(user, None)
            removed = [player]
        else:
            removed = players.pop(user, [])
        store.write_json(DATA_FILE, players)
        return removed

    async def check_player_occupied(self, player: str) -> bool:
        '''检查游戏 ID 是否已被任意用户绑定（忽略大小写）。'''
        player = player.lower()
        store = cast(ExtensionDataStore, extension.data)
        players = store.read_json(DATA_FILE) or {}
        return any(
            player in (bp.lower() for bp in bounded_players)
            for bounded_players in players.values()
        )


def get_player_service() -> PlayerService | None:
    '''获取全局注册的玩家绑定服务（未绑定/未注册时返回 None）。'''
    if extension.api is None:
        return None
    return extension.api.get(PlayerService)
