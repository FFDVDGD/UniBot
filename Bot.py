import signal
import importlib
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
    from Scripts.Managers import data_manager, plugin_manager, server_manager, version_manager, webui_manager

    await version_manager.init()
    server_manager.init()
    data_manager.load()
    plugin_manager.load()

    if config.webui.enabled:
        await webui_manager.init()
        rate_limiter.start()


@driver.on_shutdown
async def shutdown() -> None:
    from Scripts.Api.Limiter import rate_limiter
    from Scripts.Managers import data_manager

    rate_limiter.stop()
    await data_manager.save()


def register_adapters(driver, adapters: list[dict]) -> None:
    '''注册已配置的 NoneBot 适配器。'''
    for adapter in adapters:
        try:
            module = importlib.import_module(adapter['module_name'])
        except ImportError:
            logger.warning(f'导入适配器模块 {adapter["module_name"]} 失败，已跳过！')
            continue
        adapter_class = getattr(module, 'Adapter', None)
        if adapter_class is None:
            logger.warning(f'适配器模块 {adapter["module_name"]} 未包含 Adapter 类，已跳过！')
            continue
        driver.register_adapter(adapter_class)


def load_plugins(plugins: list[str | dict]) -> None:
    '''加载已启用的 NoneBot 插件。'''
    for plugin in plugins:
        module_name = plugin if isinstance(plugin, str) else plugin.get('module_name', '')
        enabled = plugin if isinstance(plugin, str) else plugin.get('enabled', True)
        if module_name and enabled:
            nonebot.load_plugin(module_name)


def exit_on_sigterm(_signal_number: int, _frame: object) -> None:
    '''使用预期退出码结束机器人进程。'''
    raise SystemExit(Process.get_exit_code())


def main():
    '''初始化并运行机器人进程。'''
    # NoneBot 初始化必须在本地模块导入之前完成。
    from Scripts.Config import config as bot_config
    from Scripts.Managers import environment_manager, webui_manager

    environment_manager.init()
    register_adapters(driver, environment_manager.nonebot_config.get('adapters', []))
    load_plugins(environment_manager.nonebot_config.get('plugins', []))

    if bot_config.webui.enabled:
        webui_manager.mount(nonebot.get_app())

    LOG_PATH.mkdir(exist_ok=True)
    logger.add(LOG_PATH / '{time}.log', rotation='1 day')
    signal.signal(signal.SIGTERM, exit_on_sigterm)
    nonebot.run()


if __name__ == '__main__':
    main()
