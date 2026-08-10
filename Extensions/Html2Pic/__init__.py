"""
html2pic 渲染引擎扩展。

将 HTML+CSS 渲染为 PNG 字节，作为默认引擎与回退引擎。
依赖 `html2pic` 库，经 `Extension.toml` 的 `[dependencies].python` 声明，
由框架自动同步到 `pyproject.toml` 的 `extensions` 可选组。
"""

import asyncio
import logging
from io import BytesIO

from html2pic import Html2Pic

from Scripts.Extensions import BaseRenderer, Extension


# logging.basicConfig() 污染 root logger，导入时清理一次）。
logging.getLogger().handlers.clear()
# 唯一扩展实例，能力经实例装饰器登记；元数据以 Extension.toml 为准
extension = Extension(types=('render',))


@extension.register_renderer
class Html2PicRenderer(BaseRenderer):
    """使用 html2pic 库渲染 HTML+CSS 为 PNG 字节。"""

    name = 'html2pic'

    async def setup(self) -> None:
        """无外部资源需要初始化。"""

    async def render(self, html: str, css: str) -> bytes:
        """渲染为 PNG 字节（在线程池中执行同步 html2pic 调用）。"""
        return await self._render_sync(html, css)

    async def shutdown(self) -> None:
        """无外部资源需要清理。"""

    @staticmethod
    async def _render_sync(html: str, css: str) -> bytes:
        """在线程池中执行同步 html2pic 渲染。"""

        def do_render() -> bytes:
            renderer = Html2Pic(html, css)
            image = renderer.render()
            pil_image = image.to_pillow()
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG', compress_level=1)
            return buffer.getvalue()

        return await asyncio.to_thread(do_render)
