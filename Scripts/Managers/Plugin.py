import time

import nonebot
from nonebot.log import logger

from Scripts.Network import request


class PluginManager:
    '''插件管理器，管理 pyproject.toml 中登记的插件、依赖插件与插件市场'''

    # 市场数据缓存时长（秒）
    MARKET_CACHE_TTL = 600
    # 插件市场注册表地址（NoneBot 官方插件市场）
    MARKET_URL = 'https://registry.nonebot.dev/plugins.json'

    market_cache: list = []
    market_cache_time: float = 0

    def load(self):
        '''记录插件管理器已完成初始化。'''
        logger.success('加载插件管理器完毕！')

    def _configured_plugins(self) -> list[dict]:
        '''获取 pyproject.toml 中登记的插件配置。'''
        from Scripts.Managers import environment_manager

        configured_plugins = []
        for plugin in environment_manager.nonebot_config.get('plugins', []):
            if isinstance(plugin, str):
                configured_plugins.append({'module_name': plugin, 'enabled': True})
            elif plugin.get('module_name'):
                configured_plugins.append(plugin)
        return configured_plugins

    @staticmethod
    def _can_disable(module_name: str) -> bool:
        return (
            module_name.startswith('Plugins.Commands.')
            or module_name.startswith('Plugins.Expand.')
            or not module_name.startswith('Plugins.')
        )

    @staticmethod
    def _plugin_info(plugin, configured: dict | None = None) -> dict:
        metadata = plugin.metadata if plugin else None
        if not plugin:
            assert configured is not None
        module_name = plugin.module_name if plugin else configured['module_name']
        extra = metadata.extra if metadata else {}
        return {
            'name': plugin.name if plugin else module_name.rsplit('.', 1)[-1],
            'module_name': module_name,
            'display_name': metadata.name if metadata else module_name.rsplit('.', 1)[-1],
            'version': extra.get('version', '') if metadata else '',
            'description': metadata.description if metadata else '',
            'author': extra.get('author', '') if metadata else '',
            'homepage': metadata.homepage if metadata else '',
            'enabled': configured.get('enabled', True) if configured else True,
            'type': 'builtin' if module_name.startswith('Plugins.') else 'external',
            'can_disable': PluginManager._can_disable(module_name),
            'dependencies': [],
            'config_schema': {},
        }

    def get_installed_plugins(self) -> list[dict]:
        '''获取登记插件和未登记依赖插件的详细信息。'''
        loaded_plugins = {plugin.module_name: plugin for plugin in nonebot.get_loaded_plugins()}
        plugins = []
        configured_modules = set()
        for configured in self._configured_plugins():
            module_name = configured['module_name']
            configured_modules.add(module_name)
            plugins.append(self._plugin_info(loaded_plugins.get(module_name), configured))
        for module_name, plugin in loaded_plugins.items():
            if module_name not in configured_modules:
                info = self._plugin_info(plugin)
                info['type'] = 'dependency'
                info['can_disable'] = False
                plugins.append(info)
        return plugins

    def get_plugin_detail(self, name: str) -> dict | None:
        '''获取指定插件详情'''
        for plugin in self.get_installed_plugins():
            if plugin['name'] == name or plugin['module_name'] == name:
                return plugin
        return None

    async def set_enabled(self, name: str, enabled: bool) -> bool:
        '''设置可管理插件的启停状态，重启后生效。'''
        plugin = self.get_plugin_detail(name)
        if not plugin or not plugin['can_disable']:
            return False
        from Scripts.Managers import environment_manager

        environment_manager.set_plugin_enabled(plugin['module_name'], enabled)
        return True

    # ===== 插件市场 =====

    async def fetch_market(self, force: bool = False) -> list[dict]:
        '''获取插件市场数据（带缓存），请求失败时返回空列表'''
        now = time.time()
        if (
            not force
            and self.market_cache
            and now - self.market_cache_time < self.MARKET_CACHE_TTL
        ):
            return self.market_cache
        data = await request(self.MARKET_URL)
        if not isinstance(data, list):
            logger.warning('获取插件市场数据失败，可能为网络问题！')
            return self.market_cache
        self.market_cache = [item for item in data if isinstance(item, dict)]
        self.market_cache_time = now
        logger.success(f'刷新插件市场数据成功！共收录 {len(self.market_cache)} 个插件。')
        return self.market_cache

    async def install(self, project_link: str, module_name: str, version: str = '') -> tuple[bool, str]:
        '''从市场安装插件：登记依赖并注册插件，重启后由 Watchdog 自动 uv sync 安装'''
        from Scripts.Managers import environment_manager

        package = f'{project_link}=={version}' if version else project_link
        environment_manager.add_dependency(package)
        environment_manager.add_plugin(module_name)
        logger.success(f'登记插件 {project_link} 成功！')
        return True, '安装成功，重启后生效'

    async def upgrade(self, project_link: str, module_name: str, version: str = '') -> tuple[bool, str]:
        '''升级市场插件：更新依赖登记并确保注册，重启后由 Watchdog 自动 uv sync 更新'''
        from Scripts.Managers import environment_manager

        package = f'{project_link}=={version}' if version else project_link
        environment_manager.remove_dependency(project_link)
        environment_manager.add_dependency(package)
        environment_manager.set_plugin_enabled(module_name, True)
        logger.success(f'登记升级插件 {project_link} 成功！')
        return True, '升级成功，重启后生效'

    async def uninstall(self, project_link: str, module_name: str) -> tuple[bool, str]:
        '''卸载市场插件：移除登记，重启后由 Watchdog 自动 uv sync 卸载'''
        from Scripts.Managers import environment_manager

        environment_manager.remove_plugin(module_name)
        environment_manager.remove_dependency(project_link)
        logger.success(f'登记卸载插件 {project_link} 成功！')
        return True, '卸载成功，重启后生效'


plugin_manager = PluginManager()
