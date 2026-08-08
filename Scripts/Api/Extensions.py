'''扩展系统 WebUI REST 路由：已安装扩展、配置、启停、渲染引擎与主题。'''

from fastapi import APIRouter, Depends, HTTPException, Request

from Scripts.Api.Config.Router import TOML_PATH
from Scripts.Config import Config, config, reload_config
from Scripts.Extensions import extension_manager, market_manager
from Scripts.Render import invalidate_environment
from .Auth import get_current_user, require_role

router = APIRouter(prefix='/api/extensions', tags=['Extensions'])


def _mask_config(extension) -> dict:
    '''获取扩展配置并脱敏密钥字段（只返回“已配置”状态）。

    未绑定/禁用的扩展无配置，返回空字典。
    '''
    if extension.config is None:
        return {}
    raw = extension.config.value.model_dump()
    masked = {}
    for key, value in raw.items():
        if 'key' in key.lower() or 'secret' in key.lower() or 'token' in key.lower():
            masked[key] = '<configured>' if value else ''
        else:
            masked[key] = value
    return masked


def _get_extension(extension_id: str):
    '''按 id 获取扩展，不存在则抛 404。'''
    extension = extension_manager.registry.get(extension_id)
    if extension is None:
        raise HTTPException(status_code=404, detail=f'扩展 {extension_id} 不存在')
    return extension


@router.get('', summary='已安装扩展列表')
async def get_extensions(current_user: dict = Depends(get_current_user)):
    '''获取已安装扩展列表（类型/版本/状态）。'''
    return {'code': 0, 'data': extension_manager.get_extensions(), 'message': 'ok'}


@router.get('/market', summary='扩展市场列表')
async def get_market(force: bool = False, current_user: dict = Depends(get_current_user)):
    '''获取扩展市场注册表（带缓存），支持 force 强制刷新。'''
    data = await market_manager.fetch_market(force=force)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/market/install', summary='从市场安装扩展')
async def install_market_extension(request: Request, user: dict = Depends(require_role('admin'))):
    '''从市场下载并安装/升级扩展，重启后生效。'''
    try:
        body = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    extension_id = (body or {}).get('id', '')
    version = (body or {}).get('version', '')
    if not extension_id:
        return {'code': 1, 'data': None, 'message': '缺少扩展 id'}
    success, message = await market_manager.install(extension_id, version)
    return {'code': 0 if success else 1, 'data': None, 'message': message}


@router.get('/items/{extension_id}', summary='扩展详情与配置 schema')
async def get_extension_detail(extension_id: str, current_user: dict = Depends(get_current_user)):
    '''获取扩展详情 + 配置 schema（供 WebUI 动态表单）。'''
    extension = _get_extension(extension_id)
    detail = extension_manager.get_extension_info(extension_id)
    detail['config_schema'] = extension.get_config_schema()
    return {'code': 0, 'data': detail, 'message': 'ok'}


@router.post('/{extension_id}/enable', summary='启用扩展')
async def enable_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    '''启用扩展（写 Config/Extensions.toml，重启生效）。'''
    _get_extension(extension_id)
    extension_manager.set_enabled(extension_id, True)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.post('/{extension_id}/disable', summary='禁用扩展')
async def disable_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    '''禁用扩展（写 Config/Extensions.toml，重启生效）。'''
    _get_extension(extension_id)
    extension_manager.set_enabled(extension_id, False)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/{extension_id}/config', summary='读取扩展配置')
async def get_extension_config(extension_id: str, current_user: dict = Depends(get_current_user)):
    '''读取扩展配置（密钥字段脱敏）。'''
    extension = _get_extension(extension_id)
    return {'code': 0, 'data': _mask_config(extension), 'message': 'ok'}


@router.patch('/{extension_id}/config', summary='更新扩展配置')
async def patch_extension_config(extension_id: str, request: Request, user: dict = Depends(require_role('admin'))):
    '''更新扩展配置，校验失败返回字段级错误且不修改原配置。'''
    extension = _get_extension(extension_id)
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    if not extension.config:
        return {'code': 1, 'data': None, 'message': '扩展当前未加载，无法修改配置'}
    try:
        extension.update_config(patch_data)
    except Exception as error:
        return {'code': 1, 'data': None, 'message': f'配置校验失败：{error}'}
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/{extension_id}', summary='卸载扩展')
async def uninstall_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    '''卸载市场扩展（删除目录并清理安装状态，重启后生效）。'''
    success, message = await market_manager.uninstall(extension_id)
    if not success:
        return {'code': 1, 'data': None, 'message': message}
    return {'code': 0, 'data': None, 'message': message}


@router.get('/renderers', summary='可用渲染引擎列表')
async def get_renderers(current_user: dict = Depends(get_current_user)):
    '''返回已注册渲染引擎列表（含当前选中）。'''
    renderers = [
        {'name': name, 'current': name == config.image.renderer}
        for name in extension_manager.renderers
    ]
    return {'code': 0, 'data': renderers, 'message': 'ok'}


@router.post('/renderers/switch', summary='切换渲染引擎')
async def switch_renderer(request: Request, user: dict = Depends(require_role('admin'))):
    '''切换渲染引擎并写回 Config.toml。'''
    try:
        body = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    name = (body or {}).get('name', '')
    if name not in extension_manager.renderers:
        return {'code': 1, 'data': None, 'message': f'渲染引擎 {name} 不存在'}
    _patch_image_config('renderer', name)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/themes', summary='可用主题列表')
async def get_themes(current_user: dict = Depends(get_current_user)):
    '''返回可用主题列表（含当前选中）。'''
    themes = [
        {'name': theme_id, 'current': theme_id == config.image.theme}
        for theme_id in extension_manager.themes
    ]
    return {'code': 0, 'data': themes, 'message': 'ok'}


@router.post('/themes/switch', summary='切换主题')
async def switch_theme(request: Request, user: dict = Depends(require_role('admin'))):
    '''切换主题并立即使模板缓存失效。'''
    try:
        body = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    theme_name = (body or {}).get('name', '')
    if theme_name != 'default' and theme_name not in extension_manager.themes:
        return {'code': 1, 'data': None, 'message': f'主题 {theme_name} 不存在'}
    _patch_image_config('theme', theme_name)
    invalidate_environment()
    return {'code': 0, 'data': None, 'message': 'ok'}


def _patch_image_config(field_name: str, value: str) -> None:
    '''将 image.<field> 写入 Config.toml 并热更新内存配置。'''
    current_data = config.model_dump()
    current_data['image'] = {**current_data['image'], field_name: value}

    import tomlkit
    try:
        toml_document = tomlkit.parse(TOML_PATH.read_text('Utf-8'))
    except FileNotFoundError:
        toml_document = tomlkit.document()
    image_doc = toml_document.get('image')
    if image_doc is None or not isinstance(image_doc, dict):
        image_doc = tomlkit.table()
        toml_document['image'] = image_doc
    image_doc[field_name] = value
    TOML_PATH.write_text(tomlkit.dumps(toml_document), encoding='Utf-8')

    reload_config()