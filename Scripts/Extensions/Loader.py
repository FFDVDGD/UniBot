'''扩展发现、依赖拓扑排序与导入加载。'''

import importlib
import importlib.util
from pathlib import Path

from nonebot.log import logger

from Scripts.Extensions.Base import (
    CompatibilityError,
    DependencyError,
    Extension,
    ExtensionMetadata,
    ExtensionState,
    LoadError,
    ManifestError,
    get_unibot_version,
    parse_manifest,
)
from Scripts.Extensions.Command import (
    command_manager,
)
from Scripts.Extensions.Renderer import RendererRegistry
from Scripts.Extensions.Service import ServiceRegistry
from Scripts.Extensions.Storage import ExtensionConfigStore, ExtensionDataStore

# 扩展目录根
EXTENSIONS_DIR = Path('Extensions')
CONFIG_ROOT = Path('Config') / 'Exs'
DATA_ROOT = Path('Data') / 'Exs'

# 框架约定文件名
MANIFEST_FILE = 'Extension.toml'
STATE_FILE = 'State.toml'


def get_extension(path: str, *, cls=None) -> Extension:
    '''创建多文件扩展实例。

    自动定位扩展目录（由入口模块 __file__ 推断），解析并严格校验
    `Extension.toml`，再创建带有 `ExtensionMetadata` 的 `Extension` 实例。
    可通过 `cls` 指定行为类。工厂不得执行全局注册或启动外部资源。
    '''
    module_path = Path(path).resolve()
    directory = module_path.parent
    extension_id = directory.name
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.exists():
        raise ManifestError(f'扩展 {extension_id} 缺少 {MANIFEST_FILE}！')
    manifest = parse_manifest(manifest_path.read_text('Utf-8'))
    if manifest.extension.id != extension_id:
        raise ManifestError(
            f'扩展 id {manifest.extension.id} 与目录名 {extension_id} 不一致！'
        )
    behavior_cls = cls if cls is not None else Extension
    extension = behavior_cls()
    extension.metadata = ExtensionMetadata(manifest)
    return extension


class ExtensionLoader:
    '''扫描、校验、排序并加载扩展。'''

    def __init__(self, manager) -> None:
        self.manager = manager
        # 发现的扩展元信息：id -> {manifest, directory}
        self._discovered: dict[str, dict] = {}
        # 已加载的扩展实例（按拓扑顺序）
        self.extensions: list[Extension] = []

    def load(self) -> list[Extension]:
        '''执行完整加载流程：发现 -> 校验 -> 拓扑排序 -> 导入 -> 声明 -> on_load。'''
        self._discover()
        self._validate_all()
        order = self._topological_sort()
        self._import_and_load(order)
        return self.extensions

    # ===== 发现 =====

    def _discover(self) -> None:
        '''扫描 Extensions/ 目录并解析清单。'''
        if not EXTENSIONS_DIR.exists():
            logger.info('扩展目录不存在，跳过扩展加载！')
            return
        for directory in EXTENSIONS_DIR.iterdir():
            if not directory.is_dir() or directory.name.startswith('.'):
                continue
            manifest_path = directory / MANIFEST_FILE
            if not manifest_path.exists():
                logger.warning(f'扩展目录 {directory.name} 缺少 {MANIFEST_FILE}，已跳过！')
                continue
            try:
                manifest = parse_manifest(manifest_path.read_text('Utf-8'))
            except ManifestError as error:
                logger.error(f'扩展 {directory.name} 清单解析失败：{error}，已跳过！')
                continue
            extension_id = manifest.extension.id
            # 校验 id 与目录名完全一致（含大小写）
            if extension_id != directory.name:
                logger.error(
                    f'扩展 id {extension_id} 与目录名 {directory.name} 不一致，已跳过！'
                )
                continue
            self._discovered[extension_id] = {'manifest': manifest, 'directory': directory}
            logger.debug(f'发现扩展 {extension_id} v{manifest.extension.version}！')

    # ===== 校验 =====

    def _validate_all(self) -> None:
        '''校验发现的扩展：版本兼容性、Python 依赖、入口模块命名。'''
        for extension_id, info in self._discovered.items():
            manifest = info['manifest']
            directory = info['directory']
            self._validate_compatibility(extension_id, manifest)
            self._validate_entry_module(extension_id, directory)

    def _validate_compatibility(self, extension_id: str, manifest) -> None:
        '''校验扩展与当前 UniBot 版本的兼容性。'''
        from packaging.specifiers import SpecifierSet

        constraint = manifest.compatibility.unibot
        try:
            specifier = SpecifierSet(constraint)
        except Exception as error:
            raise CompatibilityError(
                f'扩展 {extension_id} 的版本约束非法：{constraint}（{error}）'
            ) from error
        current_version = get_unibot_version()
        if current_version and current_version not in specifier:
            raise CompatibilityError(
                f'扩展 {extension_id} 需要 UniBot {constraint}，当前为 {current_version}！'
            )

    @staticmethod
    def _validate_entry_module(extension_id: str, directory: Path) -> None:
        '''校验入口模块文件名与扩展 id 一致（含大小写）。'''
        entry_module = directory / f'{extension_id}.py'
        if not entry_module.exists():
            raise ManifestError(
                f'扩展 {extension_id} 缺少入口模块 {extension_id}.py，与目录名不一致！'
            )

    # ===== 拓扑排序 =====

    def _topological_sort(self) -> list[str]:
        '''建立依赖图并进行拓扑排序，检测缺失依赖与循环依赖。'''
        extension_ids = set(self._discovered.keys())
        order: list[str] = []
        visited: dict[str, int] = {}  # 0=临时标记, 1=已加入

        def visit(extension_id: str, stack: list[str]) -> None:
            if visited.get(extension_id) == 1:
                return
            if visited.get(extension_id) == 0:
                cycle = ' -> '.join(stack + [extension_id])
                raise DependencyError(f'检测到循环依赖：{cycle}')
            visited[extension_id] = 0
            stack.append(extension_id)
            dependencies = self._discovered[extension_id]['manifest'].dependencies.extensions
            for dependency_id in dependencies:
                if dependency_id not in extension_ids:
                    raise DependencyError(
                        f'扩展 {extension_id} 依赖缺失：{dependency_id}！'
                    )
                visit(dependency_id, stack)
            stack.pop()
            visited[extension_id] = 1
            order.append(extension_id)

        for extension_id in extension_ids:
            visit(extension_id, [])
        return order

    # ===== 导入与加载 =====

    def _import_and_load(self, order: list[str]) -> None:
        '''按拓扑顺序导入模块、获取扩展实例并执行声明与 on_load。'''
        for extension_id in order:
            info = self._discovered[extension_id]
            try:
                extension = self._import_extension(extension_id, info['directory'])
            except Exception as error:
                logger.error(f'导入扩展 {extension_id} 失败：{error}，已跳过！')
                continue
            extension.metadata = ExtensionMetadata(info['manifest'])
            extension.state = ExtensionState.loaded
            extension.api = ServiceRegistry(self.manager)
            extension.config_path_root = CONFIG_ROOT / extension_id
            extension.data_path_root = DATA_ROOT / extension_id
            extension.config_store = ExtensionConfigStore(extension.config_path_root)
            extension.data_store = ExtensionDataStore(extension.data_path_root)
            # 加载配置
            if extension.config_model is not None:
                extension.config = extension.config_store.load(extension.config_model)
            # 执行声明：实例化装饰器收集的能力类并统一提交
            try:
                self._commit_services(extension)
                self._commit_commands(extension_id, extension)
                self._commit_renderers(extension)
            except Exception as error:
                extension.mark_failed(f'声明阶段失败：{error}')
                continue
            self.extensions.append(extension)
            self.manager.registry[extension_id] = extension
            logger.success(f'加载扩展 {extension_id} v{extension.metadata.version} 完毕！')

    @staticmethod
    def _import_extension(extension_id: str, directory: Path) -> Extension:
        '''导入扩展入口模块并获取 extension 实例。'''
        module_name = f'Extensions.{extension_id}.{extension_id}'
        module = importlib.import_module(module_name)
        extension = getattr(module, 'extension', None)
        if extension is None:
            raise LoadError(f'扩展 {extension_id} 未导出 extension 实例！')
        if not isinstance(extension, Extension):
            raise LoadError(f'扩展 {extension_id} 的 extension 不是 Extension 子类！')
        return extension

    def _commit_services(self, extension: Extension) -> None:
        '''实例化并提交装饰器声明的服务到扩展的 api 注册表。'''
        for service_cls in extension.services:
            service = service_cls()
            name = getattr(service, 'name', '') or service_cls.__name__
            extension.api.register(name, service)

    def _commit_renderers(self, extension: Extension) -> None:
        '''实例化并提交装饰器声明的渲染器到全局注册表。'''
        renderer_registry = RendererRegistry(self.manager)
        for renderer_cls in extension.renderers:
            renderer_registry.register(renderer_cls())

    def _commit_commands(self, extension_id: str, extension: Extension) -> None:
        for command_cls in extension.commands:
            command = command_cls()
            command_id = f'extension:{extension_id}:{command.name}'
            command_manager.register_command(command, command_id)


# 供单例使用
loader = ExtensionLoader