import asyncio
import html
import json
import re
from pathlib import Path
from random import choice

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, TemplateNotFound
from nonebot.log import logger

from .Config import config

# 兼容段：为保持一致保留 html2pic 相关日志清理（Stretchable 依赖会调用

RESOURCES_DIR = Path(__file__).parent.parent / 'Resources'
FONT_PATH: Path = RESOURCES_DIR / 'Font.ttf'

# 支持的图片扩展名
_IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
# 匹配字符串中的 random("...") 或 random('...') 调用
_RANDOM_PATTERN = re.compile(r"""random\(\s*['"]([^'"]+)['"]\s*\)""")


def random_image(directory_path: str) -> str:
    """
    从指定目录中随机挑选一张图片，返回完整的 url("...") 字符串。

        在 CSS 模板中可写作：background-image: random("./Resources/Backgrounds");
        路径相对于项目根目录（即 Resources 的父目录）解析。
    """
    path = Path(directory_path)
    if not path.is_absolute():
        # 以项目根目录（Bot.py 所在目录）为基准解析相对路径
        path = RESOURCES_DIR.parent / path
    if not path.is_dir():
        logger.warning(f'RandomImage 错误！目录不存在: {path}')
        return ''
    images = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES]
    if not images:
        logger.warning(f'RandomImage 错误！目录中没有图片: {path}')
        return ''
    # 返回相对项目根目录的 POSIX 路径，与现有 background 配置保持一致
    chosen = choice(images)
    return f'url("{str(chosen.absolute())}")'


def resolve_random(value: str) -> str:
    """
    解析字符串中的 random("dir") 调用，替换为实际的随机图片 url("...")。

        用于让 Config.toml 等静态配置也能使用 random 语法，
        例如：background = 'random("./Resources/Backgrounds")'。
    """
    if not value or 'random(' not in value:
        return value
    return _RANDOM_PATTERN.sub(lambda m: random_image(m.group(1)), value)


def _build_environment() -> Environment:
    """
    构建 Jinja2 环境：当前主题优先，默认主题（DefaultTheme）回退。

    当前主题（`config.image.theme`）从扩展管理器主题注册表取模板目录；
    指定主题缺失时回退默认主题扩展（theme_name='default'），两者都缺失时抛错。
    """
    loaders = []
    # 函数内导入：Scripts.Extensions 初始化时可能反向触发本模块（经扩展模块 -> Globals），
    # 延迟到调用时再取 extension_manager，避免导入期循环依赖
    from Scripts.Extensions import extension_manager

    templates_dir = extension_manager.themes.get(config.image.theme)
    if templates_dir is not None:
        loaders.append(FileSystemLoader(str(templates_dir)))
    else:
        logger.warning(f'主题 {config.image.theme} 不存在，回退默认主题！')
    # 默认主题（DefaultTheme 扩展）作为最终回退
    default_dir = extension_manager.themes.get('default')
    if default_dir is not None and (not loaders or default_dir != templates_dir):
        loaders.append(FileSystemLoader(str(default_dir)))
    if not loaders:
        raise RuntimeError('未找到可用模板主题，请确认 DefaultTheme 扩展已启用！')
    environment = Environment(loader=ChoiceLoader(loaders), enable_async=True)
    environment.globals['random'] = random_image
    return environment


# 当前生效的 Jinja2 环境；切换主题时置空以触发重建
environment: Environment | None = None


def _get_environment() -> Environment:
    """获取当前环境，惰性重建（支持主题热切换）。"""
    global environment
    if environment is None:
        environment = _build_environment()
    return environment


def invalidate_environment() -> None:
    """使当前 Jinja2 环境失效，下次渲染按新主题重建（主题热切换）。"""
    global environment
    environment = None


async def render(html: str, css: str) -> bytes:
    """委托当前渲染引擎渲染 HTML+CSS 为 PNG 字节。"""
    # 函数内导入：与 _build_environment 同理，避免导入期循环依赖
    from Scripts.Extensions import extension_manager

    return await extension_manager.renderer_manager.render(html, css, config.image.renderer)


def encode_context(context: dict) -> dict:
    string = json.dumps(context)
    return json.loads(html.escape(string, False))


async def load_style(name: str, **context) -> str:
    """加载 base.css + 模板专属 css，并通过 Jinja2 异步渲染。"""
    env = _get_environment()
    parts = []
    for css_name in ('Base.css', f'{name}/{name}.css'):
        try:
            template = env.get_template(css_name)
            parts.append(await template.render_async(**context))
        except TemplateNotFound:
            continue
    return '\n'.join(parts)


async def render_template(template_name: str, size: tuple[int, int], **kwargs) -> bytes:
    """
    渲染模板为 PNG 图片字节

        template_name: 模板名称，如 'List'，对应主题模板目录下的 List/List.html 和 List.css
        size: (width, height)。
    """
    width, height = size
    background = config.image.background or 'linear-gradient(150deg, #2e4a30 0%, #1d3524 55%, #12241a 100%)'
    background = resolve_random(background)
    context = dict(
        width=width,
        height=height,
        background=background,
        font_uri=str(FONT_PATH),
        **encode_context(kwargs),
    )
    env = _get_environment()
    template = env.get_template(f'{template_name}/{template_name}.html')
    html_content, css_content = await asyncio.gather(
        template.render_async(**context),
        load_style(template_name, **context),
    )
    return await render(html_content, css_content)
