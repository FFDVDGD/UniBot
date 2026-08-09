"""
适配器驱动依赖自动同步测试。

验证方案 item：安装/卸载适配器时，merge_driver / shrink_driver 会把驱动对应的
底层依赖包（如 websockets）同步写入 / 移除出 pyproject.toml 的 dependencies。
"""

import pytest

from Scripts.Api.Config import Driver
from Scripts.Managers.Config import ConfigManager


class FakeConfigManager:
    """模拟 ConfigManager 的依赖与 .env 读写接口。"""

    def __init__(self) -> None:
        self.environment = {'DRIVER': '~fastapi'}
        self.dependencies = ['nonebot2[fastapi]>=2.2.1', 'httpx>=0.28.1']
        self.pyproject = {'tool': {'nonebot': {'adapters': []}}}

    def update_env(self, new: dict) -> None:
        self.environment.update(new)

    def add_dependency(self, package: str) -> None:
        bases = {ConfigManager._package_base(dependency) for dependency in self.dependencies}
        if ConfigManager._package_base(package) not in bases:
            self.dependencies.append(package)

    def remove_dependency(self, package: str) -> None:
        self.dependencies = [
            dependency for dependency in self.dependencies if ConfigManager._package_base(dependency) != package
        ]

    def read_pyproject(self) -> dict:
        return self.pyproject


@pytest.fixture()
def fake_manager(monkeypatch):
    """用假 ConfigManager 替换 Driver 模块内的依赖。"""
    fake = FakeConfigManager()
    monkeypatch.setattr(Driver, 'config_manager', fake)
    return fake


def test_merge_driver_adds_driver_packages(fake_manager):
    """合并驱动时，对应底层依赖包被写入 dependencies。"""
    new_driver, added = Driver.merge_driver(['~httpx', '~websockets'])

    assert new_driver == '~fastapi+~httpx+~websockets'
    assert added == ['~httpx', '~websockets']
    assert 'websockets' in fake_manager.dependencies


def test_merge_driver_does_not_duplicate_existing_package(fake_manager):
    """已声明的驱动底层包（httpx）不会被重复添加。"""
    Driver.merge_driver(['~httpx'])

    assert fake_manager.dependencies.count('httpx>=0.28.1') == 1
    assert 'httpx' not in fake_manager.dependencies


def test_merge_driver_skips_base_driver(fake_manager):
    """BASE_DRIVER（~fastapi）无需显式声明依赖，不写入。"""
    Driver.merge_driver(['~fastapi'])

    assert 'fastapi' not in fake_manager.dependencies


def test_shrink_driver_removes_driver_only(fake_manager):
    """卸载冗余驱动时只更新 DRIVER，不移除依赖声明（避免误删核心依赖）。"""
    fake_manager.dependencies.append('websockets')
    fake_manager.environment = {'DRIVER': '~fastapi+~websockets'}

    new_driver, removed = Driver.shrink_driver(['~websockets'])

    assert new_driver == '~fastapi'
    assert removed == ['~websockets']
    # 依赖声明被保留，避免误删仍被其他依赖引用的包
    assert 'websockets' in fake_manager.dependencies


def test_shrink_driver_keeps_core_dependencies(fake_manager):
    """移除驱动时不影响核心依赖（nonebot2、httpx）。"""
    fake_manager.environment = {'DRIVER': '~fastapi+~httpx+~websockets'}

    Driver.shrink_driver(['~httpx', '~websockets'])

    assert 'nonebot2[fastapi]>=2.2.1' in fake_manager.dependencies
    assert 'httpx>=0.28.1' in fake_manager.dependencies


def test_get_driver_package_mapping():
    """驱动标记到底层包的映射完整。"""
    assert Driver.get_driver_package('~websockets') == 'websockets'
    assert Driver.get_driver_package('~httpx') == 'httpx'
    assert Driver.get_driver_package('~aiohttp') == 'aiohttp'
    assert Driver.get_driver_package('~quart') == 'quart'
    assert Driver.get_driver_package('~fastapi') is None
