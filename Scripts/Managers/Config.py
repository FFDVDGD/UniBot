import sys
from contextlib import suppress
from json import JSONDecodeError, dumps, loads
from pathlib import Path

import tomlkit
from nonebot.log import logger


class ConfigManager:
    mapping: list = []
    environment: dict = {}

    env_path: Path = Path('.env')
    pyproject_path: Path = Path('pyproject.toml')
    messages_path: Path = Path('Config') / 'Messages.toml'

    # pyproject.toml 数据
    version: str = ''
    webui_version: str = ''
    nonebot_config: dict = {}
    pyproject_data: dict = {}

    def init(self):
        """加载 .env 和 pyproject.toml 配置。"""
        self.load_env()
        self.load_pyproject()

    def load_env(self):
        """加载 .env 配置文件（可重复调用，会重置内存缓存）。"""
        if not self.env_path.exists():
            logger.error('没有找到配置文件！请重新下载后重试。')
            sys.exit(1)
        self.mapping = []
        self.environment = {}
        file_content = self.env_path.read_text('Utf-8')
        for line in file_content.split('\n'):
            line = line.strip()
            if line.startswith('#') or (not line):
                self.mapping.append(line)
                continue
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            with suppress(JSONDecodeError):
                value = loads(value)
            self.environment[key] = value
            self.mapping.append(key)
        logger.success('预加载配置文件完毕！文件已载入到内存中。')

    def load_pyproject(self):
        """加载 pyproject.toml 配置（版本号、NoneBot 适配器/插件等）。"""
        if not self.pyproject_path.exists():
            logger.error('没有找到 pyproject.toml！请重新下载后重试。')
            sys.exit(1)
        self.pyproject_data = tomlkit.parse(self.pyproject_path.read_text('Utf-8'))
        self.update_pyproject_cache()
        logger.success('加载 pyproject.toml 完毕！')

    def update_pyproject_cache(self):
        """更新 pyproject.toml 派生配置缓存。"""
        self.version = self.pyproject_data.get('project', {}).get('version', '')
        tools = self.pyproject_data.get('tool', {})
        self.webui_version = tools.get('unibot', {}).get('webui_version', '')
        self.nonebot_config = tools.get('nonebot', {})

    # ===== .env 操作 =====

    def read_env(self) -> dict:
        """获取 .env 配置字典。"""
        return self.environment

    def update_env(self, new: dict):
        """更新 .env 配置并写回文件。"""
        logger.info(f'正在更新配置 {new}')
        for key, value in new.items():
            self.environment[key] = value
            if key not in self.mapping:
                self.mapping.append(key)
        self.write_env()

    def write_env(self):
        """将 .env 配置写回文件。"""
        logger.info('正在写入配置……')
        lines = []
        for line in self.mapping:
            if line.startswith('#') or (not line):
                lines.append(line)
                continue
            lines.append(f'{line}={dumps(self.environment[line], ensure_ascii=False)}')
        self.env_path.write_text('\n'.join(lines), encoding='Utf-8')
        logger.success('写入配置成功！手动重启机器人后修改才会生效。')

    def write_env_raw(self, content: str):
        """以原始文本内容写回 .env 文件，并同步内存缓存。"""
        self.env_path.write_text(content, encoding='Utf-8')
        self.load_env()
        logger.success('写入配置成功！手动重启机器人后修改才会生效。')

    # ===== pyproject.toml 操作 =====

    def read_pyproject(self) -> dict:
        """读取内存中的 pyproject.toml 完整内容。"""
        return self.pyproject_data

    def write_pyproject(self, data: dict):
        """更新缓存并写回 pyproject.toml（保留注释和格式）。"""
        self.pyproject_path.write_text(tomlkit.dumps(data), encoding='Utf-8')
        self.pyproject_data = data
        self.update_pyproject_cache()

    def add_adapter(self, name: str, module_name: str) -> bool:
        """添加适配器，返回是否成功（False 表示已存在）。"""
        data = self.read_pyproject()
        adapters = data.setdefault('tool', {}).setdefault('nonebot', {}).setdefault('adapters', [])
        if any(adapter['module_name'] == module_name for adapter in adapters):
            return False
        adapters.append({'name': name, 'module_name': module_name})
        self.write_pyproject(data)
        return True

    def remove_adapter(self, module_name: str):
        """移除适配器（从 pyproject.toml 中删除）。"""
        data = self.read_pyproject()
        adapters = data.get('tool', {}).get('nonebot', {}).get('adapters', [])
        data['tool']['nonebot']['adapters'] = [adapter for adapter in adapters if adapter['module_name'] != module_name]
        self.write_pyproject(data)

    @staticmethod
    def _package_base(dependency: str) -> str:
        """从依赖字符串中提取包名（去除 extras 与版本约束）。"""
        for separator in ('[', '>', '<', '~', '!', '='):
            if separator in dependency:
                dependency = dependency.split(separator, 1)[0]
        return dependency.strip()

    def get_dependencies(self) -> list[str]:
        """获取 pyproject.toml 中登记的依赖列表。"""
        dependencies = self.read_pyproject().get('project', {}).get('dependencies', [])
        return list(dependencies)

    def remove_dependency(self, package: str):
        """从 pyproject.toml 的 dependencies 中移除指定包。"""
        data = self.read_pyproject()
        dependencies = data.get('project', {}).get('dependencies', [])
        data['project']['dependencies'] = [
            dependency for dependency in dependencies if self._package_base(dependency) != package
        ]
        self.write_pyproject(data)

    def add_dependency(self, package: str):
        """向 pyproject.toml 的 dependencies 中添加包（不重复）。"""
        data = self.read_pyproject()
        dependencies = data.setdefault('project', {}).setdefault('dependencies', [])
        package_bases = {self._package_base(dependency) for dependency in dependencies}
        if self._package_base(package) not in package_bases:
            dependencies.append(package)
            self.write_pyproject(data)

    def add_plugin(self, module_name: str) -> bool:
        """添加插件，返回是否成功（False 表示已存在）。"""
        data = self.read_pyproject()
        plugins = data.setdefault('tool', {}).setdefault('nonebot', {}).setdefault('plugins', [])
        if any(
            plugin == module_name or isinstance(plugin, dict) and plugin.get('module_name') == module_name
            for plugin in plugins
        ):
            return False
        plugins.append({'module_name': module_name, 'enabled': True})
        self.write_pyproject(data)
        return True

    def remove_plugin(self, module_name: str):
        """移除插件。"""
        data = self.read_pyproject()
        plugins = data.get('tool', {}).get('nonebot', {}).get('plugins', [])
        data['tool']['nonebot']['plugins'] = [
            plugin
            for plugin in plugins
            if not (plugin == module_name or isinstance(plugin, dict) and plugin.get('module_name') == module_name)
        ]
        self.write_pyproject(data)

    def set_plugin_enabled(self, module_name: str, enabled: bool):
        """更新 pyproject.toml 中插件的启用状态。"""
        data = self.read_pyproject()
        plugins = data.get('tool', {}).get('nonebot', {}).get('plugins', [])
        plugin_found = False
        for index, plugin in enumerate(plugins):
            if plugin == module_name:
                plugins[index] = {'module_name': module_name, 'enabled': enabled}
                plugin_found = True
                break
            if isinstance(plugin, dict) and plugin.get('module_name') == module_name:
                plugin['enabled'] = enabled
                plugin_found = True
                break
        if not plugin_found:
            plugins.append({'module_name': module_name, 'enabled': enabled})
        data['tool']['nonebot']['plugins'] = plugins
        self.write_pyproject(data)

    # ===== Messages.toml 操作 =====

    def read_messages_raw(self) -> str:
        """读取 Messages.toml 原始文本内容。"""
        return self.messages_path.read_text('Utf-8')

    def write_messages_raw(self, content: str):
        """以原始文本写回 Messages.toml，并校验语法。"""
        tomlkit.parse(content)
        self.messages_path.write_text(content, encoding='Utf-8')
        from Scripts.Messages import reload_messages

        reload_messages()
        logger.success('消息文本已保存并重新载入！')


config_manager = ConfigManager()
