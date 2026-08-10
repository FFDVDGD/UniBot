"""渲染扩展测试（A4）：渲染器注册、RendererManager 激活/回退/清理、模板/资源注册。"""

import asyncio
from pathlib import Path

import pytest

from Scripts.Extensions import BaseRenderer, RendererManager, extension_manager
from Scripts.Extensions.Base import TemplateFieldConfig
from Scripts.Extensions.Loader import CONFIG_ROOT
from Scripts.Extensions.Renderer import (
    TemplateRegistration,
    build_template_config_model,
)
from Scripts.Extensions.Storage import ExtensionConfigStore


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

    def test_register_template(self):
        extension_manager.register_renderer(_FakeRenderer('x'))
        model = build_template_config_model('T', {})
        store = ExtensionConfigStore(Path(CONFIG_ROOT), 'T', model)
        registration = TemplateRegistration('T', Path('/tmp/templates'), (), model, store)
        extension_manager.register_template(registration)
        assert extension_manager.templates['T'] is registration
        # 重复注册覆盖且不抛异常
        extension_manager.register_template(registration)
        assert extension_manager.templates['T'] is registration

    def test_unregister_template(self):
        model = build_template_config_model('T', {})
        store = ExtensionConfigStore(Path(CONFIG_ROOT), 'T', model)
        registration = TemplateRegistration('T', Path('/tmp/templates'), (), model, store)
        extension_manager.register_template(registration)
        extension_manager.unregister_template('T')
        assert extension_manager.templates == {}

    def test_register_resources(self):
        extension_manager.register_resources('R', Path('/tmp/resources'))
        assert extension_manager.resources['R'] == Path('/tmp/resources')
        extension_manager.unregister_resources('R')
        assert extension_manager.resources == {}


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

    def test_template_reads_background_from_config(self, tmp_path):
        """模板自行从 config.background 读取背景，框架不再注入 background。"""
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        asyncio.run(manager.setup('fake'))
        template_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Templates'
        config_model = build_template_config_model(
            'Default',
            {
                'background': TemplateFieldConfig(
                    type='string',
                    default='{{ random("Default", "Backgrounds") }}',
                ),
            },
        )
        store = ExtensionConfigStore(tmp_path, 'Default', config_model)
        manager.register_template(TemplateRegistration('Default', template_root, (), config_model, store))
        # 注册背景资源包
        resources_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Resources'
        manager.register_resources('Default', resources_root)
        asyncio.run(manager.render_image('About', (600, 0), renderer='fake'))
        html, css = renderer.rendered[0]
        # random() 语法已解析为实际图片 url，且不再由框架注入 background 变量
        assert 'random(' not in css
        assert 'background-image: url("' in css

    def test_template_background_supports_jinja(self, tmp_path):
        """config.background 内嵌 {{ }} 表达式会被 Jinja 二次渲染。"""
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        asyncio.run(manager.setup('fake'))
        template_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Templates'
        config_model = build_template_config_model(
            'Default',
            {
                'background': TemplateFieldConfig(
                    type='string',
                    default='linear-gradient({{ 45 + 45 }}deg, #000 0%, #fff 100%)',
                ),
            },
        )
        store = ExtensionConfigStore(tmp_path, 'Default', config_model)
        manager.register_template(TemplateRegistration('Default', template_root, (), config_model, store))
        # 注册资源包（render_image 需要从中解析默认字体 Font.ttf）
        resources_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Resources'
        manager.register_resources('Default', resources_root)
        asyncio.run(manager.render_image('About', (600, 0), renderer='fake'))
        html, css = renderer.rendered[0]
        assert '{{' not in css
        assert 'linear-gradient(90deg' in css

    def test_config_background_calls_random_global(self, tmp_path):
        """config 内嵌 {{ random(...) }} 走 Jinja 全局函数，返回路径并自行包装 url()。"""
        renderer = _FakeRenderer('fake')
        manager = RendererManager(lambda name: renderer if name == 'fake' else None)
        asyncio.run(manager.setup('fake'))
        template_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Templates'
        config_model = build_template_config_model(
            'Default',
            {
                'background': TemplateFieldConfig(
                    type='string',
                    default='{{ random("Default", "Backgrounds") }}',
                ),
            },
        )
        store = ExtensionConfigStore(tmp_path, 'Default', config_model)
        manager.register_template(TemplateRegistration('Default', template_root, (), config_model, store))
        # 注册背景资源包
        resources_root = Path(__file__).parent.parent / 'Extensions' / 'Default' / 'Resources'
        manager.register_resources('Default', resources_root)
        asyncio.run(manager.render_image('About', (600, 0), renderer='fake'))
        html, css = renderer.rendered[0]
        assert '{{' not in css
        assert 'random(' not in css
        assert 'background-image: url("' in css
