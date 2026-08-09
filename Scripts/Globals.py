from Scripts.Config import config

# 兼容模式下的玩家列表缓存：{服务器名称: [玩家名列表]}
player_list_cache: dict[str, list[str]] = {}

# 玩家绑定服务（内置 Player 扩展），扩展加载完成后由 Bot.py 注入
player_service = None

render_template = None

if config.image.mode:
    from .Render import render_template
