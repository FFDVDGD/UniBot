'''扩展管理器单例：注册表、服务、渲染器、启停状态与加载编排。'''

from pathlib import Path

import tomlkit
from nonebot.log import logger

from . import (
    Extension,
    ExtensionState,
)
from .Loader import (
    CONFIG_EXTENSIONS_FILE,
    ExtensionLoader,
)
from .Renderer import BaseRenderer
from .Renderers import RendererManager


class ExtensionManager:
    '''扩展管理器，负责扩展生命周期、服务注册与渲染器管理。'''

    registry: dict[str, Extension] = {}
    services: dict[str, object] = {}
    renderers: dict[str, BaseRenderer] = {}
    themes: dict[str, Path] = {}

    def __init__(self) -> None:
        self.loader = ExtensionLoader(self)
        self.renderer_manager = RendererManager(self.get_renderer)

    # ===== 加载与生命周期 =====

    def load(self) -> None:
        '''发现、校验、排序并加载扩展（声明 + on_load）。'''
        self.registry.clear()
        self.loader.load()

    async def start(self) -> None:
        '''按拓扑顺序调用 on_load 与 on_enable，失败时回滚已启用扩展。'''
        for extension in self.loader.extensions:
            if extension.state is not ExtensionState.loaded:
                continue
            try:
                await extension.on_load()
                await extension.on_enable()
                if extension.api is not None:
                    await extension.api.enable()
                extension.transition(ExtensionState.enabled)
            except Exception as error:
                extension.mark_failed(str(error))
                await self._disable_extension(extension)
                await self._rollback(extension)
        # 内置 html2pic 渲染引擎由内置扩展 Html2Pic 加载并注册，此处仅完成引擎初始化
        await self.renderer_manager.setup('html2pic')
        logger.success('扩展启动完毕！')

    async def _rollback(self, failed_extension: Extension) -> None:
        '''当某个扩展启用失败时，按逆拓扑顺序回滚已启用扩展。'''
        for extension in reversed(self.loader.extensions):
            if extension is failed_extension:
                continue
            if extension.state is ExtensionState.enabled:
                await self._disable_extension(extension)
                extension.transition(ExtensionState.disabled)

    async def shutdown(self) -> None:
        '''按逆拓扑顺序释放资源，单个扩展失败不阻止其它扩展关闭。'''
        for extension in reversed(self.loader.extensions):
            if extension.state is not ExtensionState.enabled:
                continue
            await self._disable_extension(extension)
            extension.transition(ExtensionState.disabled)
        await self.renderer_manager.shutdown()

    @staticmethod
    async def _disable_extension(extension: Extension) -> None:
        '''先关闭服务再释放扩展资源，清理失败不阻止后续步骤。'''
        if extension.api is not None:
            await extension.api.disable()
        try:
            await extension.on_disable()
        except Exception as error:
            logger.error(f'扩展 {extension.id} 关闭失败：{error}！')

    # ===== 服务注册与获取 =====

    def register_service(self, name: str, service: object) -> None:
        '''注册一个 API 服务。'''
        if name in self.services:
            logger.warning(f'API 服务 {name} 重复注册，已覆盖！')
        self.services[name] = service

    def get_service(self, name: str) -> object | None:
        '''获取已注册的 API 服务，未注册返回 None。'''
        return self.services.get(name)

    # ===== 渲染器管理 =====

    def register_renderer(self, renderer: BaseRenderer) -> None:
        '''注册一个渲染引擎实例。'''
        if renderer.name:
            self.renderers[renderer.name] = renderer

    def register_theme(self, extension_id: str, templates_dir: Path) -> None:
        '''注册一个主题扩展的模板目录。'''
        self.themes[extension_id] = templates_dir

    def get_renderer(self, name: str) -> BaseRenderer | None:
        '''获取指定名称的渲染引擎实例。'''
        return self.renderers.get(name)

    # ===== 启停状态 =====

    def set_enabled(self, extension_id: str, enabled: bool) -> bool:
        '''设置扩展启停状态（写入 Config/Extensions.toml，重启生效），返回是否成功。'''
        config_path = CONFIG_EXTENSIONS_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict = {}
        if config_path.exists():
            try:
                data = tomlkit.parse(config_path.read_text('Utf-8'))
            except Exception:
                data = {}
        extension_config = dict(data.get(extension_id, {}))
        extension_config['enabled'] = enabled
        data[extension_id] = extension_config
        config_path.write_text(tomlkit.dumps(data), encoding='Utf-8')
        logger.info(f'扩展 {extension_id} 已设置为 {"启用" if enabled else "禁用"}，重启后生效！')
        return True

    # ===== 展示信息 =====

    def get_extension_info(self, extension_id: str) -> dict:
        '''获取扩展的展示信息（供 WebUI 使用）。'''
        extension = self.registry.get(extension_id)
        if extension is None or extension.metadata is None:
            return {}
        return {
            'id': extension.metadata.id,
            'name': extension.metadata.name,
            'version': extension.metadata.version,
            'author': extension.metadata.author,
            'description': extension.metadata.description,
            'types': [entry.value for entry in extension.metadata.types],
            'state': extension.state.value,
            'config_schema': extension.get_config_schema(),
        }

    def get_extensions(self) -> list[dict]:
        '''获取全部已加载扩展的展示信息。'''
        return [self.get_extension_info(extension_id) for extension_id in self.registry]


# 单例
extension_manager = ExtensionManager()