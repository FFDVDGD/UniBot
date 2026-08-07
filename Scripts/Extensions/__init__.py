'''UniBot 扩展系统框架包。'''

from .Base import (
    CompatibilityError,
    DependencyError,
    Extension,
    ExtensionError,
    ExtensionManifest,
    ExtensionMetadata,
    ExtensionState,
    ExtensionType,
    LoadError,
    ManifestError,
    RenderConfig,
    RenderKind,
    StorageError,
    parse_manifest,
)
from .Command import (
    Argument,
    Command,
    CommandError,
    CommandFieldError,
    CommandManager,
    Handler,
    ImageHandler,
    SubCommand,
    UNSET,
    command_manager,
    discover_commands,
)
from .Loader import (
    CONFIG_ROOT,
    DATA_ROOT,
    EXTENSIONS_DIR,
    ExtensionLoader,
    get_extension,
)
from .Service import Service, ServiceRegistry
from .Renderer import BaseRenderer, RendererRegistry
from .Renderers import Html2PicRenderer, RendererManager
from .Storage import (
    CONFIG_FILE_NAME,
    ExtensionConfigStore,
    ExtensionDataStore,
    RESERVED_STATE_FILE,
)

__all__ = [
    # Base
    'CompatibilityError',
    'DependencyError',
    'Extension',
    'ExtensionError',
    'ExtensionManifest',
    'ExtensionMetadata',
    'ExtensionState',
    'ExtensionType',
    'LoadError',
    'ManifestError',
    'RenderConfig',
    'RenderKind',
    'StorageError',
    'parse_manifest',
    # Command
    'Argument',
    'Command',
    'CommandError',
    'CommandFieldError',
    'CommandManager',
    'Handler',
    'ImageHandler',
    'SubCommand',
    'UNSET',
    'command_manager',
    'discover_commands',
    # Loader
    'CONFIG_ROOT',
    'DATA_ROOT',
    'EXTENSIONS_DIR',
    'ExtensionLoader',
    'get_extension',
    # Service
    'Service',
    'ServiceRegistry',
    # Renderer
    'BaseRenderer',
    'RendererRegistry',
    # Renderers
    'Html2PicRenderer',
    'RendererManager',
    # Storage
    'CONFIG_FILE_NAME',
    'ExtensionConfigStore',
    'ExtensionDataStore',
    'RESERVED_STATE_FILE',
]