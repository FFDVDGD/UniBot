"""UniBot 扩展系统框架包。"""

from .Base import (
    Extension,
    ExtensionManifest,
    ExtensionMetadata,
    ExtensionState,
    ExtensionType,
    RenderConfig,
    RenderKind,
    manifest_from_attributes,
    parse_manifest,
)
from .Command import (
    UNSET,
    Argument,
    Command,
    CommandManager,
    Handler,
    ImageHandler,
    SubCommand,
    command_manager,
    discover_commands,
)
from .Errors import (
    CommandError,
    CommandFieldError,
    CompatibilityError,
    DependencyError,
    ExtensionError,
    ExtensionNotBoundError,
    LoadError,
    ManifestError,
    StorageError,
)
from .Loader import (
    BUILTIN_DIR,
    CONFIG_EXTENSIONS_FILE,
    CONFIG_ROOT,
    DATA_ROOT,
    EXTENSIONS_DIR,
    STATES_FILE,
    STATES_ROOT,
    ExtensionLoader,
)
from .Manager import ExtensionManager, extension_manager
from .Market import (
    ExtensionInstallState,
    MarketExtension,
    MarketRelease,
    extract_market_package,
    safe_extract_zip,
)
from .MarketManager import ExtensionMarketManager, market_manager
from .Renderer import BaseRenderer, RendererManager, RendererRegistry
from .Service import Service, ServiceRegistry
from .Storage import (
    RESERVED_STATE_FILE,
    ExtensionConfigStore,
    ExtensionDataStore,
)

__all__ = [
    # Base
    'CompatibilityError',
    'DependencyError',
    'Extension',
    'ExtensionError',
    'ExtensionManifest',
    'ExtensionMetadata',
    'ExtensionNotBoundError',
    'ExtensionState',
    'ExtensionType',
    'LoadError',
    'ManifestError',
    'RenderConfig',
    'RenderKind',
    'StorageError',
    'manifest_from_attributes',
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
    'BUILTIN_DIR',
    'CONFIG_EXTENSIONS_FILE',
    'CONFIG_ROOT',
    'DATA_ROOT',
    'EXTENSIONS_DIR',
    'ExtensionLoader',
    'STATES_FILE',
    'STATES_ROOT',
    # Manager
    'ExtensionManager',
    'extension_manager',
    # Market
    'ExtensionInstallState',
    'MarketExtension',
    'MarketRelease',
    'extract_market_package',
    'safe_extract_zip',
    # MarketManager
    'ExtensionMarketManager',
    'market_manager',
    # Service
    'Service',
    'ServiceRegistry',
    # Renderer
    'BaseRenderer',
    'RendererManager',
    'RendererRegistry',
    # Storage
    'ExtensionConfigStore',
    'ExtensionDataStore',
    'RESERVED_STATE_FILE',
]
