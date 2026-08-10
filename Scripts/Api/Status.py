import time

import nonebot
import psutil
from fastapi import APIRouter, BackgroundTasks, Depends

from Scripts import Globals
from Scripts.Config import config
from Scripts.Managers import version_manager
from Scripts.Process import is_watchdog_process, request_restart

from .Auth import get_current_user, require_role
from .WebSocket import ws_clients

router = APIRouter(prefix='/api/status', tags=['Status'])

start_time = time.time()


def get_status_data() -> dict:
    """生成机器人运行状态数据（REST 接口与 WebSocket 推送共用）。"""
    adapter_names = list(nonebot.get_adapters().keys())
    player_service, server_service = Globals.player_service, Globals.server_service
    servers = server_service.servers if server_service else {}
    players_bound = len(player_service.players) if player_service else 0
    return {
        'version': version_manager.version,
        'latest_version': version_manager.latest_version,
        'has_update': version_manager.check_update(),
        'uptime': int(time.time() - start_time),
        'memory_mb': round(psutil.Process().memory_info().rss / 1024 / 1024, 1),
        'cpu_percent': psutil.Process().cpu_percent(interval=0.1),
        'servers_online': len(servers),
        'players_bound': players_bound,
        'adapters': adapter_names,
        'webui_enabled': config.webui.enabled,
        'ws_clients': len(ws_clients),
    }


@router.get('', summary='获取运行状态')
async def get_status(current_user: dict = Depends(get_current_user)):
    """获取机器人运行状态概览。"""
    return {'code': 0, 'data': get_status_data(), 'message': 'ok'}


@router.post('/check-update', summary='检测最新版本')
async def check_update(current_user: dict = Depends(get_current_user)):
    """主动从 GitHub 拉取最新发布版本并返回检测结果。"""
    success = await version_manager.fetch_latest()
    if not success:
        return {'code': 1, 'data': None, 'message': '检测失败，请检查网络稍后再试'}
    return {
        'code': 0,
        'data': {
            'version': version_manager.version,
            'latest_version': version_manager.latest_version,
            'has_update': version_manager.check_update(),
        },
        'message': 'ok',
    }


@router.get('/health', summary='健康检查')
async def health_check():
    """健康检查（无需认证），用于监控探针。"""
    return {
        'code': 0,
        'data': {'status': 'healthy', 'started_at': start_time},
        'message': 'ok',
    }


@router.post('/restart', summary='重启机器人', dependencies=[Depends(require_role('admin'))])
async def restart_bot(background_tasks: BackgroundTasks):
    """通知守护进程优雅重启机器人。"""
    if not is_watchdog_process():
        return {
            'code': 1,
            'data': None,
            'message': '机器人未通过 Watchdog 启动，无法自动重启',
        }

    background_tasks.add_task(request_restart)
    return {
        'code': 0,
        'data': {'started_at': start_time},
        'message': '机器人正在重启',
    }
