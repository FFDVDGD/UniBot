from typing import TYPE_CHECKING

from Scripts.Config import config

if TYPE_CHECKING:
    from Scripts.Extensions.Builtin.Services.Players import PlayerService
    from Scripts.Extensions.Builtin.Services.Servers import ServerService

# 兼容模式下的玩家列表缓存：{服务器名称: [玩家名列表]}
player_list_cache: dict[str, list[str]] = {}

# 玩家绑定服务，由 Players 内置扩展在启停时维护
player_service: 'PlayerService | None' = None

# Minecraft 服务器服务，由 Servers 内置扩展在启停时维护
server_service: 'ServerService | None' = None

# 图片渲染入口，由 Scripts.Render 提供；仅图片模式开启时注入
# （命令的 image_handler 只在图片模式调用，关闭时为 None 不会被执行）
render_template = None

if config.image.mode:
    from .Render import render_template  # noqa: F401 故意 re-export 供全局使用
