'''UniBot 扩展系统：扩展基类、元数据、状态机与错误模型。'''

from copy import deepcopy
from enum import Enum
from typing import Any

from nonebot.log import logger
from pydantic import BaseModel, ConfigDict, Field

from Scripts.Extensions.Service import ServiceRegistry


# ===== 错误模型 =====

class ExtensionError(Exception):
    '''扩展系统错误基类。'''


class ManifestError(ExtensionError):
    '''清单元数据解析或校验失败。'''


class CompatibilityError(ExtensionError):
    '''扩展与当前 UniBot 版本不兼容。'''


class DependencyError(ExtensionError):
    '''扩展依赖缺失或存在循环依赖。'''


class LoadError(ExtensionError):
    '''扩展模块导入或初始化失败。'''


class StorageError(ExtensionError):
    '''扩展配置或数据读写失败。'''


class ExtensionState(str, Enum):
    '''扩展生命周期状态。'''

    discovered = 'discovered'   # 发现目录，尚未校验
    validated = 'validated'     # 清单校验通过
    loaded = 'loaded'           # 模块导入并完成声明
    enabled = 'enabled'         # 已启用（on_enable 完成）
    disabled = 'disabled'       # 已停用
    failed = 'failed'           # 加载或启用失败


# 允许的状态迁移：状态 -> 可达状态集合
_STATE_TRANSITIONS: dict[ExtensionState, set[ExtensionState]] = {
    ExtensionState.discovered: {ExtensionState.validated, ExtensionState.failed},
    ExtensionState.validated: {ExtensionState.loaded, ExtensionState.failed},
    ExtensionState.loaded: {ExtensionState.enabled, ExtensionState.disabled, ExtensionState.failed},
    ExtensionState.enabled: {ExtensionState.disabled, ExtensionState.failed},
    ExtensionState.disabled: {ExtensionState.enabled, ExtensionState.failed},
    ExtensionState.failed: set(),
}


# ===== 清单元数据（extension.toml） =====

class ExtensionType(str, Enum):
    '''扩展类型。'''

    api = 'api'
    command = 'command'
    render = 'render'


class RenderKind(str, Enum):
    '''渲染扩展子类型。'''

    engine = 'engine'
    theme = 'theme'


class ManifestMeta(BaseModel):
    '''[manifest] 段：清单格式版本。'''

    model_config = ConfigDict(extra='forbid')

    schema_version: int = 1


class ExtensionMeta(BaseModel):
    '''[extension] 段：扩展身份信息。'''

    model_config = ConfigDict(extra='forbid')

    id: str = Field(min_length=1, pattern=r'^[A-Za-z0-9_]+$')
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    author: str = ''
    description: str = ''
    types: list[ExtensionType] = [ExtensionType.api]


class CompatibilityConfig(BaseModel):
    '''[compatibility] 段：兼容的机器人版本。'''

    model_config = ConfigDict(extra='forbid')

    unibot: str = '*'


class DependenciesConfig(BaseModel):
    '''[dependencies] 段：依赖的其他扩展与第三方 Python 依赖。'''

    model_config = ConfigDict(extra='forbid')

    extensions: list[str] = []
    python: list[str] = []


class RenderConfig(BaseModel):
    '''[render] 段（仅渲染扩展需要）。'''

    model_config = ConfigDict(extra='forbid')

    kind: list[RenderKind] = []
    theme_name: str | None = None


class ExtensionManifest(BaseModel):
    '''extension.toml 根模型，严格校验（未知字段直接阻止加载）。'''

    model_config = ConfigDict(extra='forbid')

    manifest: ManifestMeta = ManifestMeta()
    extension: ExtensionMeta
    compatibility: CompatibilityConfig = CompatibilityConfig()
    dependencies: DependenciesConfig = DependenciesConfig()
    render: RenderConfig = RenderConfig()


class ExtensionMetadata:
    '''从清单解析出的便捷元数据对象，供扩展代码与框架使用。'''

    def __init__(self, manifest: ExtensionManifest) -> None:
        self.manifest = manifest
        extension = manifest.extension
        self.id = extension.id
        self.name = extension.name
        self.version = extension.version
        self.author = extension.author
        self.description = extension.description
        self.types = list(extension.types)
        self.unibot_constraint = manifest.compatibility.unibot
        self.extension_dependencies = list(manifest.dependencies.extensions)
        self.python_dependencies = list(manifest.dependencies.python)
        self.render_kind = list(manifest.render.kind)
        self.theme_name = manifest.render.theme_name

    def to_dict(self) -> dict:
        '''转换为可序列化字典（供 WebUI 展示）。'''
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'types': [entry.value for entry in self.types],
            'unibot': self.unibot_constraint,
            'extension_dependencies': self.extension_dependencies,
            'python_dependencies': self.python_dependencies,
            'render_kind': [entry.value for entry in self.render_kind],
            'theme_name': self.theme_name,
        }


def parse_manifest(content: str) -> ExtensionManifest:
    '''解析 extension.toml 文本内容，返回严格校验后的清单。'''
    try:
        import tomllib
        data = tomllib.loads(content)
    except Exception as error:
        raise ManifestError(f'扩展清单解析失败：{error}') from error
    try:
        return ExtensionManifest.model_validate(data)
    except Exception as error:
        raise ManifestError(f'扩展清单校验失败：{error}') from error


# ===== Extension 基类 =====

class Extension:
    '''UniBot 本地扩展基类，所有扩展必须继承并实现。

    扩展通过 `@Extension.command` / `@Extension.service` / `@Extension.renderer`
    装饰器标记能力类；`__init_subclass__` 自动从扩展子类命名空间收集这些标记
    类（含继承得到的声明），存入类级 `commands` / `services` / `renderers`。
    Loader 创建实例后复制声明列表，实例化各能力类并统一提交，不产生全局注册
    副作用。
    '''

    # 装饰器标记属性名
    _COMMAND_MARK = '_extension_command'
    _SERVICE_MARK = '_extension_service'
    _RENDERER_MARK = '_extension_renderer'

    # 由扩展类声明，Loader 实例化后注入
    metadata: ExtensionMetadata
    config_model: type[BaseModel] | None = None
    config: BaseModel

    # 由 Loader 创建并注入，作用域限定在当前扩展
    config_store: Any = None
    data_store: Any = None
    config_path_root: Any = None
    data_path_root: Any = None

    # 服务注册入口与带扩展名前缀的 logger
    api: ServiceRegistry
    logger = logger

    state: ExtensionState = ExtensionState.discovered

    # 失败原因（mark_failed 时记录）
    failure_reason: str | None = None

    # 声明的能力类集合（由 __init_subclass__ 收集，Loader 实例化并提交）
    commands: list = []
    services: list = []
    renderers: list = []

    def __init_subclass__(cls, **kwargs) -> None:
        '''收集本类及继承得到的能力类声明到类级列表。'''
        super().__init_subclass__(**kwargs)
        cls.commands = list(getattr(cls, 'commands', [])) + [
            member for member in vars(cls).values()
            if getattr(member, cls._COMMAND_MARK, False)
        ]
        cls.services = list(getattr(cls, 'services', [])) + [
            member for member in vars(cls).values()
            if getattr(member, cls._SERVICE_MARK, False)
        ]
        cls.renderers = list(getattr(cls, 'renderers', [])) + [
            member for member in vars(cls).values()
            if getattr(member, cls._RENDERER_MARK, False)
        ]

    @staticmethod
    def command(command_cls):
        '''装饰器：给 Command 子类打标，供 __init_subclass__ 收集。'''
        setattr(command_cls, Extension._COMMAND_MARK, True)
        return command_cls

    @staticmethod
    def service(service_cls):
        '''装饰器：给 Service 子类打标，供 __init_subclass__ 收集。'''
        setattr(service_cls, Extension._SERVICE_MARK, True)
        return service_cls

    @staticmethod
    def renderer(renderer_cls):
        '''装饰器：给 BaseRenderer 子类打标，供 __init_subclass__ 收集。'''
        setattr(renderer_cls, Extension._RENDERER_MARK, True)
        return renderer_cls

    @property
    def id(self) -> str:
        '''扩展唯一标识（由元信息提供）。'''
        return self.metadata.id

    def __init__(self) -> None:
        '''初始化扩展实例。不能在此产生全局注册副作用。'''
        if self.config_model is None:
            self.config_model = self._default_config_model()

    @staticmethod
    def _default_config_model() -> type[BaseModel]:
        '''未声明 config_model 时使用空配置模型，不接受未声明字段。'''
        class EmptyConfig(BaseModel):
            model_config = ConfigDict(extra='forbid')
        return EmptyConfig

    # ===== 声明提交（Loader 调用，将能力类实例提交给全局注册表） =====

    def register_command(self, command_cls) -> None:
        '''记录命令类到声明列表（供 Loader 实例化并提交）。'''
        self.commands.append(command_cls)

    def register_service(self, service_cls) -> None:
        '''记录服务类到声明列表（供 Loader 实例化并提交）。'''
        self.services.append(service_cls)

    def register_renderer(self, renderer_cls) -> None:
        '''记录渲染器类到声明列表（供 Loader 实例化并提交）。'''
        self.renderers.append(renderer_cls)

    # ===== 生命周期 =====

    async def on_load(self) -> None:
        '''实例创建后、声明完成后调用（可选覆盖）。'''

    async def on_enable(self) -> None:
        '''声明确认后启动外部资源（可选覆盖）。'''

    async def on_disable(self) -> None:
        '''释放外部资源（可选覆盖）。'''

    # ===== 配置工具 =====

    def get_config_schema(self) -> dict:
        '''返回扩展配置的 JSON Schema（供 WebUI 动态生成表单）。'''
        return self.config_model.model_json_schema()

    def update_config(self, values: dict) -> BaseModel:
        '''校验并持久化配置；校验失败抛出异常且不修改原配置。'''
        updated = self.config_model.model_validate(values)
        self.config_store.save(updated)
        self.config = updated
        return updated

    # ===== 状态机 =====

    def transition(self, target: ExtensionState) -> None:
        '''按状态机迁移扩展状态，非法迁移抛出错误。'''
        allowed = _STATE_TRANSITIONS.get(self.state, set())
        if target not in allowed:
            raise ExtensionError(
                f'扩展 {self.id} 状态迁移非法：{self.state.value} -> {target.value}'
            )
        self.state = target

    def mark_failed(self, reason: str) -> None:
        '''将扩展标记为失败状态，并记录原因。'''
        self.logger.error(f'扩展 {self.id} 加载失败：{reason}！')
        self.state = ExtensionState.failed
        self.failure_reason = reason

    def clone(self) -> 'Extension':
        '''创建当前扩展的浅拷贝（用于覆盖机制，保留业务逻辑但重置状态）。'''
        return deepcopy(self)


def get_unibot_version() -> str:
    '''获取当前 UniBot 版本号（去除前缀 v）。'''
    from Scripts.Managers import config_manager

    return config_manager.version.lstrip('v')