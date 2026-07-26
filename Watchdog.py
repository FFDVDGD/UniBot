import os
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path

from nonebot.log import logger

from Scripts.Process import RESTART_EXIT_CODE, WATCHDOG_ENVIRONMENT

MAX_RESTART_ATTEMPTS = 3
RESTART_WINDOW_SECONDS = 60

BOT_PATH = Path('Bot.py')
CONFIG_PATH = Path('Config.toml')
PYPROJECT_PATH = Path('pyproject.toml')

EXTRA_CONFIG_FIELDS = {
    'ai': ('ai', 'enabled'),
    'image': ('image', 'mode'),
    'webui': ('webui', 'enabled'),
}


def read_toml(path: Path) -> dict:
    '''读取 TOML 文件。'''
    with path.open('rb') as file:
        return tomllib.load(file)


def get_enabled_extras() -> list[str]:
    '''获取当前配置中已启用的可选功能。'''
    config = read_toml(CONFIG_PATH)
    return [
        extra
        for extra, (section, field) in EXTRA_CONFIG_FIELDS.items()
        if config.get(section, {}).get(field, False)
    ]


def get_dependency_state() -> tuple[list, dict, tuple[str, ...]]:
    '''获取影响 uv 同步结果的依赖声明。'''
    project = read_toml(PYPROJECT_PATH).get('project', {})
    return (
        project.get('dependencies', []),
        project.get('optional-dependencies', {}),
        tuple(get_enabled_extras()),
    )


def sync_dependencies() -> None:
    '''使用 uv 同步项目依赖和已启用的可选功能。'''
    command = ['uv', 'sync']
    for extra in get_enabled_extras():
        command.extend(('--extra', extra))

    logger.info(f'检测到依赖声明变化，正在执行：{" ".join(command)}')
    try:
        subprocess.run(command, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        logger.error(f'同步项目依赖失败：{error}')
        raise SystemExit(1) from error
    logger.success('同步项目依赖完成！')


def run() -> None:
    '''守护机器人进程，处理异常退出与 WebUI 重启请求。'''
    restart_attempts = 0
    restart_window_started_at = time.monotonic()
    shutdown_requested = False
    dependency_state = get_dependency_state()
    bot_environment = os.environ.copy()
    bot_environment[WATCHDOG_ENVIRONMENT] = '1'

    while True:
        bot_process = subprocess.Popen(
            [sys.executable, str(BOT_PATH), *sys.argv[1:]],
            env=bot_environment,
            start_new_session=True,
        )

        def forward_signal(signal_number: int, _frame: object) -> None:
            nonlocal shutdown_requested
            shutdown_requested = True
            if bot_process.poll() is None:
                bot_process.send_signal(signal_number)

        signal.signal(signal.SIGINT, forward_signal)
        signal.signal(signal.SIGTERM, forward_signal)
        exit_code = bot_process.wait()

        if exit_code == RESTART_EXIT_CODE:
            current_dependency_state = get_dependency_state()
            if current_dependency_state != dependency_state:
                sync_dependencies()
                dependency_state = current_dependency_state
            restart_attempts = 0
            restart_window_started_at = time.monotonic()
            logger.info('收到 WebUI 重启请求，正在重新启动机器人！')
            continue

        if shutdown_requested or exit_code in (0, -signal.SIGINT, -signal.SIGTERM):
            logger.info('机器人已正常退出，不再重启！')
            return

        current_time = time.monotonic()
        if current_time - restart_window_started_at > RESTART_WINDOW_SECONDS:
            restart_window_started_at = current_time
            restart_attempts = 0

        if restart_attempts >= MAX_RESTART_ATTEMPTS:
            logger.error(f'机器人在 {RESTART_WINDOW_SECONDS} 秒内已重试 {MAX_RESTART_ATTEMPTS} 次，停止重启！')
            raise SystemExit(exit_code)

        restart_attempts += 1
        logger.warning(f'机器人异常退出（退出码 {exit_code}），正在进行第 {restart_attempts} 次自动重启！')


if __name__ == '__main__':
    run()