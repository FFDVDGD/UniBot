import time

import nonebot
import psutil
from fastapi import APIRouter, BackgroundTasks, Depends

from Scripts.Config import config
from Scripts.Managers import data_manager, server_manager, version_manager
from Scripts.Process import is_watchdog_process, request_restart
from .Auth import get_current_user, require_role
from .WebSocket import ws_clients

router = APIRouter(prefix='/api/status', tags=['Status'])

start_time = time.time()


@router.get('', summary='获取运行状态')
async def get_status(current_user: dict = Depends(get_current_user)):
    '''获取机器人运行状态概览'''
    adapter_names = list(nonebot.get_adapters().keys())
    servers = server_manager.servers or {}
    return {
        'code': 0,
        'data': {
            'version': version_manager.version,
            'uptime': int(time.time() - start_time),
            'memory_mb': round(psutil.Process().memory_info().rss / 1024 / 1024, 1),
            'cpu_percent': psutil.Process().cpu_percent(interval=0.1),
            'servers_online': len(servers),
            'servers_total': len(servers),
            'players_bound': len(data_manager.players),
            'adapters': adapter_names,
            'webui_enabled': config.webui.get('enabled', False) if isinstance(config.webui, dict) else config.webui.enabled,
            'ws_clients': len(ws_clients),
        },
        'message': 'ok',
    }


@router.get('/health', summary='健康检查')
async def health_check():
    '''健康检查（无需认证），用于监控探针'''
    return {
        'code': 0,
        'data': {'status': 'healthy', 'started_at': start_time},
        'message': 'ok',
    }


@router.post('/restart', summary='重启机器人', dependencies=[Depends(require_role('admin'))])
async def restart_bot(background_tasks: BackgroundTasks):
    '''通知守护进程优雅重启机器人。'''
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
