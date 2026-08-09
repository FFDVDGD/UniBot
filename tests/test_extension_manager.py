"""ExtensionManager 测试：拓扑排序、生命周期、失败隔离、启停状态（验证点 9、14、8）。"""

import asyncio
from typing import override

import pytest
import tomlkit

from Scripts.Extensions import Extension, ExtensionState, Service, ServiceRegistry, extension_manager


def _bind_registry(extension: Extension) -> ServiceRegistry:
    """为生命周期测试建立最小服务注册表绑定。"""
    registry = ServiceRegistry(extension_manager)
    extension._api = registry
    extension._bound = True
    return registry


class _GoodExt(Extension):
    def __init__(self, ext_id: str) -> None:
        super().__init__()
        self._ext_id = ext_id
        _bind_registry(self)
        self.enabled = False
        self.disabled = False

    @property
    @override
    def id(self) -> str:
        return self._ext_id

    @override
    async def on_enable(self) -> None:
        self.enabled = True

    @override
    async def on_disable(self) -> None:
        self.disabled = True


class _FailingExt(Extension):
    def __init__(self, ext_id: str) -> None:
        super().__init__()
        self._ext_id = ext_id
        _bind_registry(self)

    @property
    @override
    def id(self) -> str:
        return self._ext_id

    @override
    async def on_enable(self) -> None:
        raise RuntimeError('boom')


class _TypedService(Service):
    name = 'typed'


class _LifecycleService(Service):
    """记录服务生命周期调用。"""

    name = 'lifecycle'

    def __init__(self) -> None:
        self.enabled = False
        self.disabled = False

    @override
    async def on_enable(self) -> None:
        self.enabled = True

    @override
    async def on_disable(self) -> None:
        self.disabled = True


class _ServiceExt(Extension):
    def __init__(self, ext_id: str, service: Service) -> None:
        super().__init__()
        self._ext_id = ext_id
        registry = _bind_registry(self)
        registry.register(service.name or type(service).__name__, service)

    @property
    @override
    def id(self) -> str:
        return self._ext_id


# ===== 服务注册 =====


class TestServices:
    def test_register_and_get_service(self):
        service = object()
        extension_manager.register_service('my_svc', service)
        assert extension_manager.get_service('my_svc') is service
        assert extension_manager.get_service('missing') is None

    def test_duplicate_service_overwrites(self):
        extension_manager.register_service('svc', object())
        new_service = object()
        extension_manager.register_service('svc', new_service)
        assert extension_manager.get_service('svc') is new_service

    def test_get_service_by_type(self):
        registry = ServiceRegistry(extension_manager)
        service = _TypedService()
        registry.register(_TypedService.name, service)

        assert registry.get(_TypedService) is service

    def test_get_missing_service_by_type(self):
        registry = ServiceRegistry(extension_manager)

        assert registry.get(_TypedService) is None

    def test_get_service_by_type_rejects_wrong_runtime_type(self):
        registry = ServiceRegistry(extension_manager)
        registry.register(_TypedService.name, object())

        with pytest.raises(TypeError, match='API 服务 typed 的类型不是 _TypedService'):
            registry.get(_TypedService)


# ===== 生命周期 =====


class TestLifecycle:
    def test_start_enables_extensions_in_order(self):
        a = _GoodExt('A')
        b = _GoodExt('B')
        # 模拟 Loader 已加载：状态进入 loaded
        a.state = ExtensionState.loaded
        b.state = ExtensionState.loaded
        extension_manager.loader.extensions = [a, b]
        asyncio.run(extension_manager.start())
        assert a.enabled and b.enabled
        assert a.state is ExtensionState.enabled
        assert b.state is ExtensionState.enabled

    def test_failure_marks_failed_and_does_not_crash(self):
        good = _GoodExt('Good')
        failing = _FailingExt('Bad')
        good.state = ExtensionState.loaded
        failing.state = ExtensionState.loaded
        # extending list so rollback tries to disable good
        extension_manager.loader.extensions = [good, failing]
        asyncio.run(extension_manager.start())
        assert failing.state is ExtensionState.failed
        # rollback disables already-enabled extensions
        assert good.disabled is True

    def test_shutdown_disables_in_reverse_order(self):
        a = _GoodExt('A')
        b = _GoodExt('B')
        a.enabled = b.enabled = True
        a.state = ExtensionState.enabled
        b.state = ExtensionState.enabled
        extension_manager.loader.extensions = [a, b]
        asyncio.run(extension_manager.shutdown())
        assert a.disabled and b.disabled
        assert a.state is ExtensionState.disabled
        assert b.state is ExtensionState.disabled

    def test_service_lifecycle_follows_extension(self):
        service = _LifecycleService()
        ext = _ServiceExt('Svc', service)
        ext.state = ExtensionState.loaded
        extension_manager.loader.extensions = [ext]
        asyncio.run(extension_manager.start())
        assert service.enabled is True
        assert service.disabled is False
        assert ext.state is ExtensionState.enabled
        asyncio.run(extension_manager.shutdown())
        assert service.disabled is True
        assert ext.state is ExtensionState.disabled


# ===== 启停状态文件 =====


class TestSetEnabled:
    def test_set_enabled_writes_config_file(self, tmp_path, monkeypatch):
        import Scripts.Extensions.Manager as ext_mod

        # 将 Extension 模块内的 CONFIG_EXTENSIONS_FILE 常量指向临时目录
        config_file = tmp_path / 'Extensions.toml'
        monkeypatch.setattr(ext_mod, 'CONFIG_EXTENSIONS_FILE', config_file)
        extension_manager.set_enabled('WeatherExt', True)
        assert config_file.exists()
        data = tomlkit.parse(config_file.read_text('Utf-8'))
        assert data['WeatherExt']['enabled'] is True

    def test_set_enabled_merges_multiple_extensions(self, tmp_path, monkeypatch):
        import Scripts.Extensions.Manager as ext_mod

        config_file = tmp_path / 'Extensions.toml'
        monkeypatch.setattr(ext_mod, 'CONFIG_EXTENSIONS_FILE', config_file)
        extension_manager.set_enabled('WeatherExt', True)
        extension_manager.set_enabled('List', False)
        data = tomlkit.parse(config_file.read_text('Utf-8'))
        assert data['WeatherExt']['enabled'] is True
        assert data['List']['enabled'] is False
