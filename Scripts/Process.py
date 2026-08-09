import os
import signal

RESTART_EXIT_CODE = 75
WATCHDOG_ENVIRONMENT = 'UNIBOT_WATCHDOG'

exit_code = 0


def is_watchdog_process() -> bool:
    """检查当前机器人是否由守护进程启动。"""
    return os.environ.get(WATCHDOG_ENVIRONMENT) == '1'


def get_exit_code() -> int:
    """获取机器人进程的预期退出码。"""
    return exit_code


def request_restart() -> None:
    """记录重启退出码，并触发框架优雅关闭。"""
    global exit_code
    exit_code = RESTART_EXIT_CODE
    os.kill(os.getpid(), signal.SIGTERM)
