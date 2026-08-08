'''渲染扩展测试（A4）：渲染器注册、RendererManager 激活/回退/清理、主题注册。'''

import asyncio

import pytest

from Scripts.Extensions import BaseRenderer, RendererManager, extension_manager


class _FakeRenderer(BaseRenderer):

    def __init__(self, name: str) -> None:
        self.name = name
        self.setup_called = False
        self.shutdown_called = False
        self.rendered = []

    async def setup(self) -> None:
        self.setup_called = True

    async def render(self, html: str, css: str) -> bytes:
        self.rendered.append((html, css))
        return f'{self.name}:{html}:{css}'.encode()

    async def shutdown(self) -> None:
        self.shutdown_called = True


# ===== 渲染器注册 =====

class TestRendererRegistration:
    def test_register_and_get_renderer(self):
        renderer = _FakeRenderer('fake')
        extension_manager.register_renderer(renderer)
        assert extension_manager.get_renderer('fake') is renderer
        assert extension_manager.get_renderer('missing') is None

    def test_register_without_name_is_ignored(self):
        class _NoName(BaseRenderer):
            async def render(self, html: str, css: str) -> bytes:
                return b''

        extension_manager.register_renderer(_NoName())
        assert extension_manager.renderers == {}

    def test_register_theme(self):
        extension_manager.register_renderer(_FakeRenderer('x'))
        extension_manager.register_theme('DarkTheme', '/tmp/templates')
        assert extension_manager.themes['DarkTheme'] == '/tmp/templates'


# ===== RendererManager =====

class TestRendererManager:
    def test_setup_activates_renderer(self):
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        asyncio.run(manager.setup('fake'))
        assert renderer.setup_called
        assert manager._active['fake'] is renderer

    def test_setup_missing_engine_falls_back_to_html2pic(self):
        # 注册一个待回退的 html2pic 假引擎
        fallback = _FakeRenderer('html2pic')
        manager = RendererManager(lambda name: fallback if name == 'html2pic' else None)
        resolved = asyncio.run(manager.setup('nonexistent'))
        assert resolved is fallback
        assert fallback.setup_called

    def test_setup_with_no_fallback_returns_none(self):
        manager = RendererManager(lambda name: None)
        assert asyncio.run(manager.setup('anything')) is None

    def test_same_renderer_not_setup_twice(self):
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer)
        asyncio.run(manager.setup('fake'))
        asyncio.run(manager.setup('fake'))
        assert renderer.setup_called
        assert len([r for r in manager._active.values() if r is renderer]) == 1

    def test_render_delegates_to_active_engine(self):
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        asyncio.run(manager.setup('fake'))
        result = asyncio.run(manager.render('<h1>x</h1>', 'body{}', name='fake'))
        assert result == b'fake:<h1>x</h1>:body{}'
        assert renderer.rendered == [('<h1>x</h1>', 'body{}')]

    def test_render_auto_setup_when_not_active(self):
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        result = asyncio.run(manager.render('a', 'b', name='fake'))
        assert renderer.setup_called
        assert result == b'fake:a:b'

    def test_shutdown_cleans_all(self):
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer)
        asyncio.run(manager.setup('fake'))
        asyncio.run(manager.shutdown())
        assert renderer.shutdown_called
        assert manager._active == {}

    def test_render_without_engine_raises(self):
        manager = RendererManager(lambda name: None)
        with pytest.raises(RuntimeError):
            asyncio.run(manager.render('a', 'b'))