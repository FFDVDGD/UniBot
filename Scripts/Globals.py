from Scripts.Config import config

uuid_caches: dict[str, str] = {}

# 兼容模式下的玩家列表缓存：{服务器名称: [玩家名列表]}
player_list_cache: dict[str, list[str]] = {}

render_template = None

if config.image.mode:
    from .Render import render_template
