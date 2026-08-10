import asyncio
import importlib
import signal
from pathlib import Path

import nonebot
from nonebot.log import logger

from Scripts import Process

LOG_PATH = Path('Logs/')

nonebot.init()
driver = nonebot.get_driver()


@driver.on_startup
async def startup() -> None:
    from Scripts.Api.Limiter import rate_limiter
    from Scripts.Config import config
    from Scripts.Extensions import extension_manager
    from Scripts.Managers import (
        data_manager,
        version_manager,
        webui_manager,
    )

    data_manager.load()

    asyncio.create_task(version_manager.init())

    if config.webui.enabled:
        await webui_manager.init()
        rate_limiter.start()

    await extension_manager.start()


@driver.on_shutdown
async def shutdown() -> None:
    from Scripts.Api.Limiter import rate_limiter
    from Scripts.Extensions import extension_manager
    from Scripts.Managers import data_manager

    await extension_manager.shutdown()
    rate_limiter.stop()
    await data_manager.save()


def register_adapters(driver, adapters: list[dict]) -> None:
    """注册已配置的 NoneBot 适配器。"""
    for adapter in adapters:
        try:
            module = importlib.import_module(adapter['module_name'])
        except ImportError:
            logger.warning(f'导入适配器模块 {adapter["module_name"]} 失败，已跳过！')
            continue
        if adapter_class := getattr(module, 'Adapter', None):
            logger.info(f'正在注册 {adapter_class} 适配器。')
            driver.register_adapter(adapter_class)
            continue
        logger.warning(f'适配器模块 {adapter["module_name"]} 未包含 Adapter 类，已跳过！')


def load_plugins(plugins: list[str | dict]) -> None:
    """加载已启用的 NoneBot 插件。"""
    for plugin in plugins:
        if isinstance(plugin, str):
            nonebot.load_plugin(plugin)
            continue
        if (module_name := plugin.get('module_name', '')) and plugin.get('enabled', True):
            nonebot.load_plugin(module_name)


def exit_on_sigterm(_signal_number: int, _frame: object) -> None:
    """使用预期退出码结束机器人进程。"""
    raise SystemExit(Process.get_exit_code())


def main():
    """初始化并运行机器人进程。"""
    # NoneBot 初始化必须在本地模块导入之前完成。
    from Scripts.Config import config as bot_config
    from Scripts.Managers import config_manager, webui_manager

    config_manager.init()
    
    register_adapters(driver, config_manager.nonebot_config.get('adapters', []))

    nonebot.load_plugin('Scripts.Plugins.Extensions')
    load_plugins(config_manager.nonebot_config.get('plugins', []))

    if bot_config.webui.enabled:
        webui_manager.mount(nonebot.get_app())

    LOG_PATH.mkdir(exist_ok=True)
    logger.add(LOG_PATH / '{time}.log', rotation='1 day')
    signal.signal(signal.SIGTERM, exit_on_sigterm)
    nonebot.run()


if __name__ == '__main__':
    main()
