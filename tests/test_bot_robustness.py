"""
Bot.py 启动健壮性测试。

验证方案：适配器加载失败（模块不存在、缺少 Adapter 类、配置不符合规范导致
实例化抛异常）时，register_adapters 应跳过失败适配器而不影响其他适配器注册，
保证整个机器人不会因此退出。
"""

from types import SimpleNamespace

import pytest

import Bot


class FakeDriver:
    """模拟 NoneBot Driver 的 register_adapter 接口（内部实例化适配器）。"""

    def __init__(self) -> None:
        self.registered = []

    def register_adapter(self, adapter_class: type) -> None:
        # 与真实 Driver 一致：实例化适配器，配置校验失败时异常向上传播且不注册。
        adapter_class(self)
        self.registered.append(adapter_class)


class BadAdapter:
    """模拟配置不符合规范时实例化抛异常的适配器。"""

    def __init__(self, driver: object, **kwargs: object) -> None:
        raise RuntimeError('配置不符合规范，实例化失败！')


class GoodAdapter:
    """模拟正常适配器。"""

    def __init__(self, driver: object, **kwargs: object) -> None:
        pass


@pytest.fixture()
def fake_import(monkeypatch):
    """替换 Bot.importlib.import_module，返回预置的假模块。"""
    fake_module = SimpleNamespace(Adapter=GoodAdapter)
    bad_module = SimpleNamespace(Adapter=BadAdapter)
    no_adapter_module = SimpleNamespace()

    def _import(module_name: str):
        if module_name == 'good.adapter':
            return fake_module
        if module_name == 'bad.adapter':
            return bad_module
        if module_name == 'no.adapter':
            return no_adapter_module
        raise ImportError(f'No module named {module_name}')

    monkeypatch.setattr(Bot.importlib, 'import_module', _import)


def test_register_adapters_skip_import_error(fake_import):
    """模块不存在时跳过并继续注册其他适配器。"""
    driver = FakeDriver()
    adapters = [
        {'module_name': 'missing.adapter'},
        {'module_name': 'good.adapter'},
    ]
    Bot.register_adapters(driver, adapters)
    assert driver.registered == [GoodAdapter]


def test_register_adapters_skip_no_adapter_class(fake_import):
    """模块缺少 Adapter 类时跳过并继续注册其他适配器。"""
    driver = FakeDriver()
    adapters = [
        {'module_name': 'no.adapter'},
        {'module_name': 'good.adapter'},
    ]
    Bot.register_adapters(driver, adapters)
    assert driver.registered == [GoodAdapter]


def test_register_adapters_skip_config_error(fake_import):
    """配置不符合规范导致实例化抛异常时跳过，机器人不退出。"""
    driver = FakeDriver()
    adapters = [
        {'module_name': 'bad.adapter'},
        {'module_name': 'good.adapter'},
    ]
    Bot.register_adapters(driver, adapters)
    assert driver.registered == [GoodAdapter]


def test_register_adapters_all_good(fake_import):
    """全部适配器正常时全部注册成功。"""
    driver = FakeDriver()
    adapters = [
        {'module_name': 'good.adapter'},
        {'module_name': 'good.adapter'},
    ]
    Bot.register_adapters(driver, adapters)
    assert driver.registered == [GoodAdapter, GoodAdapter]
