from pathlib import Path

import tomlkit
from nonebot import get_plugin_config
from pydantic import BaseModel, model_validator

TOML_PATH = Path('Config.toml')


class ImageConfig(BaseModel):
    mode: bool = False
    background: str | None = None
    renderer: str = 'html2pic'  # 当前使用的渲染引擎 name，必须是已注册的引擎
    theme: str = 'default'  # 当前主题（'default' = 内置模板，或主题扩展 id）


class AiConfig(BaseModel):
    enabled: bool = False
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    system_prompt: str | None = None


class AutoReplyConfig(BaseModel):
    enabled: bool = False
    keywords: dict[str, list[str]] | None = None


class WebUiConfig(BaseModel):
    enabled: bool = False


class Config(BaseModel):
    # NoneBot 内置配置（从 .env / 环境变量读取）
    port: int = 8000
    superusers: list[str] = []
    command_start: list[str] = ['.']

    # 自定义配置（从 config.toml 读取）
    bot_prefix: str = ''
    admin_superusers: bool = True

    command_groups: list[str] = []
    message_groups: list[str] = []

    command_minecraft_whitelist: list[str] = []
    command_minecraft_blacklist: list[str] = []

    broadcast_server: bool = True
    broadcast_player: bool = True

    sync_all_qq_message: bool = True
    sync_all_game_message: bool = False
    sync_message_between_servers: bool = True
    sync_sensitive_words: list[str] = []

    list_compatible_mode: bool = False
    whitelist_command: str = 'whitelist'

    sync_color_source: str = 'gray'
    sync_color_player: str = 'gray'
    sync_color_message: str = 'gray'

    qq_bound_max_number: int = 1

    image: ImageConfig = ImageConfig()
    ai: AiConfig = AiConfig()
    auto_reply: AutoReplyConfig = AutoReplyConfig()
    webui: WebUiConfig = WebUiConfig()

    @model_validator(mode='after')
    def normalize(self):
        self.bot_prefix = self.bot_prefix.upper() if self.bot_prefix else ''
        return self


toml_data = tomlkit.parse(TOML_PATH.read_text('Utf-8'))

merged = get_plugin_config(Config).model_dump()
merged.update(toml_data)

config = Config.model_validate(merged)


def _merge_toml(content: str) -> dict:
    """解析 Config.toml 文本内容，并合并到模型默认值上。"""
    toml_data = tomlkit.parse(content)
    merged = get_plugin_config(Config).model_dump()
    merged.update(toml_data)
    return merged


def validate_config_content(content: str) -> str | None:
    """校验 Config.toml 文本内容是否可被正确加载，返回错误信息（合法返回 None）。"""
    try:
        Config.model_validate(_merge_toml(content))
    except Exception as error:
        return f'配置校验失败：{error}'
    return None


def reload_config():
    """从磁盘重新读取 Config.toml，热更新全局 config 对象（保持对象引用不变）。"""
    updated_config = Config.model_validate(_merge_toml(TOML_PATH.read_text('Utf-8')))
    for field_name in Config.model_fields:
        setattr(config, field_name, getattr(updated_config, field_name))
