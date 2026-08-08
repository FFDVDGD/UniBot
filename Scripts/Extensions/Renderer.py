'''渲染引擎基类与渲染器注册表。'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Manager import ExtensionManager


class BaseRenderer:
    '''渲染引擎基类，所有渲染扩展必须实现。'''

    name: str = ''

    async def setup(self) -> None:
        '''初始化（启动浏览器/加载资源等）。'''

    async def render(self, html: str, css: str) -> bytes:
        '''渲染为 PNG 字节。'''
        raise NotImplementedError

    async def shutdown(self) -> None:
        '''清理资源。'''


class RendererRegistry:
    '''渲染器注册表：收集引擎与主题声明。'''

    def __init__(self, manager: ExtensionManager) -> None:
        self._manager = manager

    def register(self, renderer: BaseRenderer) -> None:
        '''注册一个渲染引擎实例。'''
        self._manager.register_renderer(renderer)

    def register_theme(self, extension_id: str, templates_dir: Path) -> None:
        '''注册一个主题扩展的模板目录。'''
        self._manager.register_theme(extension_id, templates_dir)