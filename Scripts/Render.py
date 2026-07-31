import json
import html
import logging
import asyncio
import re
from io import BytesIO
from random import choice
from pathlib import Path

from html2pic import Html2Pic
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from nonebot.log import logger

from .Config import config

# html2pic 的传递依赖 stretchable 在导入时会调用 logging.basicConfig()，
# 给 root logger 添加 StreamHandler，导致 uvicorn.access 日志被重复输出。
# 在导入 html2pic 后清理 root logger 上多余的 handler，避免日志污染。
logging.getLogger().handlers.clear()

RESOURCES_DIR = Path(__file__).parent.parent / 'Resources'
FONT_PATH: Path = RESOURCES_DIR / 'Font.ttf'
TEMPLATES_DIR = RESOURCES_DIR / 'Images'

# 支持的图片扩展名
_IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
# 匹配字符串中的 random("...") 或 random('...') 调用
_RANDOM_PATTERN = re.compile(r'''random\(\s*['"]([^'"]+)['"]\s*\)''')


def random_image(directory_path: str) -> str:
    """从指定目录中随机挑选一张图片，返回完整的 url("...") 字符串。

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
    """解析字符串中的 random("dir") 调用，替换为实际的随机图片 url("...")。

    用于让 Config.toml 等静态配置也能使用 random 语法，
    例如：background = 'random("./Resources/Backgrounds")'
    """
    if not value or 'random(' not in value:
        return value
    return _RANDOM_PATTERN.sub(lambda m: random_image(m.group(1)), value)


environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), enable_async=True)
environment.globals['random'] = random_image
# 说明：在 CSS/HTML 模板中通过 Jinja2 插值调用，形如：
#   background-image: {{ random("./Resources/Backgrounds") }};

logger.debug('图片渲染器加载完毕！')


def render(html: str, css: str) -> bytes:
    renderer = Html2Pic(html, css)
    image = renderer.render()
    pil_image = image.to_pillow()
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG', compress_level=1)
    return buffer.getvalue()


def encode_context(context: dict) -> dict:
    string = json.dumps(context)
    return json.loads(html.escape(string, False))


async def load_style(name: str, **context) -> str:
    """加载 base.css + 模板专属 css，并通过 Jinja2 异步渲染"""
    parts = []
    for css_name in ('Base.css', f'{name}/{name}.css'):
        try:
            template = environment.get_template(css_name)
            parts.append(await template.render_async(**context))
        except TemplateNotFound:
            continue
    return '\n'.join(parts)


async def render_template(template_name: str, size: tuple[int, int], **kwargs) -> bytes:
    """渲染模板为 PNG 图片字节

    template_name: 模板名称，如 'List'，对应 Resources/Images/List/List.html 和 List.css
    size: (width, height)
    """
    width, height = size
    background = config.image.background or 'linear-gradient(150deg, #2e4a30 0%, #1d3524 55%, #12241a 100%)'
    background = resolve_random(background)
    context = dict(
        width=width, height=height,
        background=background,
        font_uri=str(FONT_PATH),
        **encode_context(kwargs),
    )
    template = environment.get_template(f'{template_name}/{template_name}.html')
    html_content, css_content = await asyncio.gather(
        template.render_async(**context),
        load_style(template_name, **context),
    )
    return await asyncio.to_thread(render, html_content, css_content)
