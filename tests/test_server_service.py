"""Minecraft 服务器 API 服务测试。"""

import asyncio
from typing import Any

from Scripts import Globals
from Scripts.Extensions import extension_manager
from Scripts.Extensions.Builtin.Services import Servers


class _Adapter:
    """测试用 Minecraft 适配器。"""

    def __init__(self, bots: dict[str, Any]) -> None:
        self.bots = bots


class _Bot:
    """测试用 Minecraft Bot。"""

    def __init__(self, self_id: str) -> None:
        self.self_id = self_id


def test_server_service_lifecycle_and_selection(monkeypatch) -> None:
    first = _Bot('survival')
    second = _Bot('creative')
    monkeypatch.setattr(
        Servers,
        'get_adapter',
        lambda adapter_type: _Adapter(
            {
                first.self_id: first,
                second.self_id: second,
            }
        ),
    )
    service = Servers.ServerService()

    asyncio.run(service.on_enable())

    assert service.name == 'server'
    assert Globals.server_service is service
    assert service.check_online() is True
    assert service.get_server(1) is first
    assert service.get_server('2') is second
    assert service.get_server('creative') is second
    assert service.get_server('missing') is None

    asyncio.run(service.on_disable())
    assert service.check_online() is False
    assert Globals.server_service is None


def test_server_service_is_registered() -> None:
    extension_manager.load()

    service = extension_manager.get_service('server')

    assert isinstance(service, Servers.ServerService)
