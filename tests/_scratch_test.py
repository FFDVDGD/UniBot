"""临时验证 property 泛型 + 返回式 handler。"""

from typing import Any, Generic, TypeVar, cast

T = TypeVar('T', bound='Command')


class Command(Generic[T]):
    def __init__(self, parent: T | None = None) -> None:
        self._parent = parent

    @property
    def parent(self) -> T:
        return cast(T, self._parent)

    async def handler(self, *args: Any, **kwargs: Any) -> str | None:
        return None

    async def image_handler(self, *args: Any, **kwargs: Any) -> bytes | str | None:
        return None


class Sub(Command[T]):
    pass


class Foo(Command):
    name = 'foo'

    def foo_method(self) -> str:
        return 'foo'

    class Check(Sub['Foo']):
        async def handler(self, session: Any) -> str | None:
            return self.parent.foo_method()
