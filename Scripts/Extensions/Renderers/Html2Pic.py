'''内置 html2pic 渲染引擎（默认/回退）。

从现有 Scripts/Render.py 的同步 html2pic 逻辑迁移而来，封装为
BaseRenderer 子类，供 RendererManager 统一管理。
'''

import time
from io import BytesIO

from html2pic import Html2Pic

from Scripts.Extensions.Renderer import BaseRenderer


class Html2PicRenderer(BaseRenderer):
    '''使用 html2pic 库渲染 HTML+CSS 为 PNG 字节。'''

    name = 'html2pic'

    async def setup(self) -> None:
        '''无外部资源需要初始化。'''

    async def render(self, html: str, css: str) -> bytes:
        '''渲染为 PNG 字节（在线程池中执行同步 html2pic 调用）。'''
        return await self._render_sync(html, css)

    async def shutdown(self) -> None:
        '''无外部资源需要清理。'''

    @staticmethod
    async def _render_sync(html: str, css: str) -> bytes:
        '''在线程池中执行同步 html2pic 渲染。'''
        import asyncio

        def do_render() -> bytes:
            start = time.time()
            renderer = Html2Pic(html, css)
            image = renderer.render()
            pil_image = image.to_pillow()
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG', compress_level=1)
            return buffer.getvalue()

        return await asyncio.to_thread(do_render)