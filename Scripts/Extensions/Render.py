"""
渲染兼容层：委托 Scripts/Extensions/Renderer.py 的 RendererManager。

模板渲染/样式加载/环境失效等入口统一由 `RendererManager` 编排，本模块
仅保留旧的公共 API 形状，供内置命令与其它框架代码引用（Globals 等）。
"""

from __future__ import annotations

from ..Config import config
from .Renderer import (
    FONT_PATH,
    RESOURCES_DIR,
    encode_context,
)

__all__ = [
    'FONT_PATH',
    'RESOURCES_DIR',
    'encode_context',
    'invalidate_environment',
    'load_style',
    'render',
    'render_template',
]


def invalidate_environment() -> None:
    """使全部模板扩展的 Jinja2 环境失效（模板热切换后重建）。"""
    # 函数内导入：避免导入期循环依赖
    from . import extension_manager

    extension_manager.renderer_manager.invalidate_all()


async def render(html: str, css: str) -> bytes:
    """委托当前渲染引擎渲染 HTML+CSS 为 PNG 字节。"""
    from . import extension_manager

    return await extension_manager.renderer_manager.render(html, css, config.image.renderer)


async def load_style(name: str, **context) -> str:
    """兼容包装：使用当前模板包环境加载并渲染 Base.css + 模板 css。"""
    from . import extension_manager

    manager = extension_manager.renderer_manager
    registration = manager._select_template()
    environment = manager._get_environment(registration.extension_id)
    return await manager._load_style(environment, name, **context)


async def render_template(template_name: str, size: tuple[int, int], **kwargs) -> bytes:
    """兼容包装：渲染模板为 PNG 图片字节（委托 RendererManager.render_image）。"""
    from . import extension_manager

    return await extension_manager.renderer_manager.render_image(
        template_name,
        size,
        context=kwargs,
    )
