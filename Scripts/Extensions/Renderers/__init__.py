'''渲染器管理：管理引擎实例、并发上限、单次渲染超时与默认引擎回退。'''

import asyncio
from typing import Any

from nonebot.log import logger

from Scripts.Extensions import BaseRenderer
from Scripts.Extensions.Renderers.Html2Pic import Html2PicRenderer

__all__ = ['Html2PicRenderer', 'RendererManager']


class RendererManager:
    '''统一管理渲染引擎实例，负责 setup / render / shutdown、并发与超时。'''

    def __init__(self, get_renderer_factory: Any) -> None:
        # 从扩展管理器获取渲染引擎实例的函数：name -> BaseRenderer | None
        self._get_renderer = get_renderer_factory
        # 已 setup 的引擎实例：name -> BaseRenderer
        self._active: dict[str, BaseRenderer] = {}
        # 各引擎并发上限与单次渲染超时（秒）
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._timeouts: dict[str, float] = {}
        self._default_timeout = 60.0

    def configure(self, name: str, concurrency: int = 1, timeout: float | None = None) -> None:
        '''配置指定引擎的并发上限与单次渲染超时。'''
        self._semaphores[name] = asyncio.Semaphore(max(1, concurrency))
        if timeout is not None:
            self._timeouts[name] = timeout

    async def setup(self, name: str) -> BaseRenderer | None:
        '''初始化并启用指定引擎，失败时回退默认引擎。'''
        renderer = self._get_renderer(name)
        if renderer is None:
            logger.warning(f'渲染引擎 {name} 不存在，回退默认引擎 html2pic！')
            renderer = self._get_renderer('html2pic')
            if renderer is None:
                logger.error('默认渲染引擎 html2pic 不可用！')
                return None
            name = renderer.name
        if name in self._active:
            return renderer
        await renderer.setup()
        self._active[renderer.name] = renderer
        if renderer.name not in self._semaphores:
            self._semaphores[renderer.name] = asyncio.Semaphore(max(1, 1))
        logger.info(f'渲染引擎 {renderer.name} 已就绪！')
        return renderer

    async def render(self, html: str, css: str, name: str | None = None) -> bytes:
        '''使用指定引擎渲染 HTML+CSS 为 PNG 字节，带并发上限与超时。'''
        engine_name = name or 'html2pic'
        renderer = self._active.get(engine_name)
        if renderer is None:
            renderer = await self.setup(engine_name)
        if renderer is None:
            raise RuntimeError('没有可用的渲染引擎！')
        semaphore = self._semaphores.get(renderer.name)
        timeout = self._timeouts.get(renderer.name, self._default_timeout)
        async with semaphore:
            return await asyncio.wait_for(renderer.render(html, css), timeout=timeout)

    async def shutdown(self) -> None:
        '''清理全部已启用引擎。'''
        for renderer in self._active.values():
            try:
                await renderer.shutdown()
            except Exception as error:
                logger.error(f'渲染引擎 {renderer.name} 关闭失败：{error}！')
        self._active.clear()