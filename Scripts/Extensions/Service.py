'''API 服务基类与受限服务注册入口。

扩展通过继承 `Service` 定义可被其它扩展或内置代码复用的服务能力，
由 `@Extension.service` 装饰器标记，Loader 统一实例化并提交到全局注册表。
'''

from typing import Any


class Service:
    '''API 服务基类，扩展能力服务应继承此类。'''

    # 服务注册名（缺省使用类名），供其它扩展通过 self.api.get(name) 获取
    name: str = ''


class ServiceRegistry:
    '''扩展的服务注册入口，将服务写入全局 ExtensionManager。'''

    def __init__(self, manager) -> None:
        self._manager = manager

    def register(self, name: str, service: Any) -> None:
        '''注册一个 API 服务，供其它扩展或内置代码获取。'''
        self._manager.register_service(name, service)

    def get(self, name: str) -> Any | None:
        '''获取已注册的 API 服务（未注册返回 None）。'''
        return self._manager.get_service(name)