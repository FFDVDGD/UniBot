"""扩展系统 WebUI REST 路由：已安装扩展、配置、启停、渲染引擎与主题。"""

from fastapi import APIRouter, Depends, HTTPException, Request

from Scripts.Config import config, reload_config
from Scripts.Extensions import ExtensionType, extension_manager, market_manager
from Scripts.Managers import config_manager

from .Auth import get_current_user, require_role

router = APIRouter(prefix='/api/extensions', tags=['Extensions'])


def _mask_config(extension) -> dict:
    """获取扩展配置并脱敏密钥字段（只返回“已配置”状态）。"""
    if not extension.is_bound:
        return {}
    raw = extension.config.value.model_dump()
    masked = {}
    for key, value in raw.items():
        masked[key] = value
        if 'key' in key.lower() or 'secret' in key.lower() or 'token' in key.lower():
            masked[key] = '<configured>' if value else ''
    return masked


def _ensure_extension_exists(extension_id: str) -> None:
    """校验扩展存在（registry 或无代码包），否则抛 404。"""
    if extension_id in extension_manager.registry:
        return
    if extension_id in extension_manager.no_code_info:
        return
    raise HTTPException(status_code=404, detail=f'扩展 {extension_id} 不存在')


@router.get('', summary='已安装扩展列表')
async def get_extensions(current_user: dict = Depends(get_current_user)):
    """获取已安装扩展列表（类型/版本/状态）。"""
    return {'code': 0, 'data': extension_manager.get_extensions(), 'message': 'ok'}


@router.get('/market', summary='扩展市场列表')
async def get_market(force: bool = False, current_user: dict = Depends(get_current_user)):
    """获取扩展市场注册表（带缓存），支持 force 强制刷新。"""
    data = await market_manager.fetch_market(force=force)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/market/install', summary='从市场安装扩展')
async def install_market_extension(request: Request, user: dict = Depends(require_role('admin'))):
    """从市场下载并安装/升级扩展，重启后生效。"""
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
    """获取扩展详情 + 配置 schema（供 WebUI 动态表单，含无代码模板包）。"""
    detail = extension_manager.get_extension_info(extension_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f'扩展 {extension_id} 不存在')
    return {'code': 0, 'data': detail, 'message': 'ok'}


@router.post('/{extension_id}/enable', summary='启用扩展')
async def enable_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    """启用扩展（写 Config/Extensions.toml，重启生效）。"""
    _ensure_extension_exists(extension_id)
    extension_manager.set_enabled(extension_id, True)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.post('/{extension_id}/disable', summary='禁用扩展')
async def disable_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    """禁用扩展（写 Config/Extensions.toml，重启生效）。"""
    _ensure_extension_exists(extension_id)
    extension_manager.set_enabled(extension_id, False)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/{extension_id}/config', summary='读取扩展配置')
async def get_extension_config(extension_id: str, current_user: dict = Depends(get_current_user)):
    """读取扩展配置（密钥字段脱敏；无代码模板包读模板配置）。"""
    extension = extension_manager.registry.get(extension_id)
    if extension is not None:
        return {'code': 0, 'data': _mask_config(extension), 'message': 'ok'}
    registration = extension_manager.renderer_manager.templates.get(extension_id)
    if registration is not None:
        return {'code': 0, 'data': registration.config_store.value.model_dump(), 'message': 'ok'}
    raise HTTPException(status_code=404, detail=f'扩展 {extension_id} 不存在')


@router.patch('/{extension_id}/config', summary='更新扩展配置')
async def patch_extension_config(extension_id: str, request: Request, user: dict = Depends(require_role('admin'))):
    """更新扩展配置，校验失败返回字段级错误且不修改原配置。"""
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    extension = extension_manager.registry.get(extension_id)
    if extension is not None:
        if not extension.is_bound:
            return {'code': 1, 'data': None, 'message': '扩展当前未加载，无法修改配置'}
        try:
            extension.update_config(patch_data)
        except Exception as error:
            return {'code': 1, 'data': None, 'message': f'配置校验失败：{error}'}
        return {'code': 0, 'data': None, 'message': 'ok'}
    registration = extension_manager.renderer_manager.templates.get(extension_id)
    if registration is not None:
        try:
            registration.config_store.update(patch_data)
        except Exception as error:
            return {'code': 1, 'data': None, 'message': f'配置校验失败：{error}'}
        return {'code': 0, 'data': None, 'message': 'ok'}
    raise HTTPException(status_code=404, detail=f'扩展 {extension_id} 不存在')


@router.delete('/{extension_id}', summary='卸载扩展')
async def uninstall_extension(extension_id: str, user: dict = Depends(require_role('admin'))):
    """卸载市场扩展（删除目录并清理安装状态，重启后生效）。"""
    success, message = await market_manager.uninstall(extension_id)
    if not success:
        return {'code': 1, 'data': None, 'message': message}
    return {'code': 0, 'data': None, 'message': message}


@router.get('/renderers', summary='可用渲染引擎列表')
async def get_renderers(current_user: dict = Depends(get_current_user)):
    """返回全部渲染插件（含图片模式未开启而禁用的），标注可用性与当前选中。"""
    active_names = set(extension_manager.renderers)
    items = []
    for extension in extension_manager.registry.values():
        metadata = extension.metadata
        if ExtensionType.renderer not in metadata.types:
            continue
        name = metadata.renderer_name or metadata.id
        items.append(
            {
                'name': name,
                'current': name == config.image.renderer,
                'available': name in active_names,
                'state': extension.state.value,
                'reason': extension.failure_reason or None,
            }
        )
    items.sort(key=lambda item: (not item['available'], item['name']))
    return {'code': 0, 'data': items, 'message': 'ok'}


@router.get('/render-configs', summary='渲染插件配置列表')
async def get_render_configs(current_user: dict = Depends(get_current_user)):
    """返回所有渲染类扩展（渲染器 + 模板）的配置 schema 与当前值，供渲染设置页内联编辑。"""
    active_names = set(extension_manager.renderers)
    items = []
    # 渲染器类型扩展（含图片模式未开启而禁用的）
    for extension in extension_manager.registry.values():
        metadata = extension.metadata
        if ExtensionType.renderer not in metadata.types:
            continue
        name = metadata.renderer_name or metadata.id
        items.append(
            {
                'id': metadata.id,
                'kind': 'renderer',
                'name': metadata.name,
                'renderer_name': name,
                'current': name == config.image.renderer,
                'available': name in active_names,
                'state': extension.state.value,
                'reason': extension.failure_reason or None,
                # 未绑定扩展（图片模式未开启被禁用）无配置模型，schema 为空
                'schema': extension.get_config_schema() if extension.config_model is not None else None,
                'values': _mask_config(extension),
            }
        )
    # 模板类型扩展（无代码包）
    for extension_id, registration in extension_manager.templates.items():
        no_code = extension_manager.no_code_info.get(extension_id, {})
        items.append(
            {
                'id': extension_id,
                'kind': 'template',
                'name': no_code.get('name') or extension_id,
                'template_id': extension_id,
                'current': extension_id == config.image.template,
                'available': True,
                'state': 'enabled',
                'reason': None,
                'schema': registration.config_model.model_json_schema(),
                'values': registration.config_store.value.model_dump(mode='json'),
            }
        )
    items.sort(key=lambda item: (item['kind'] != 'renderer', not item['available'], item['id']))
    return {'code': 0, 'data': items, 'message': 'ok'}


@router.post('/renderers/switch', summary='切换渲染引擎')
async def switch_renderer(request: Request, user: dict = Depends(require_role('admin'))):
    """切换渲染引擎并写回 Config.toml。"""
    try:
        body = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    name = (body or {}).get('name', '')
    if name not in extension_manager.renderers:
        return {'code': 1, 'data': None, 'message': f'渲染引擎 {name} 不存在'}
    _patch_image_config('renderer', name)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/templates', summary='可用模板列表')
async def get_templates(current_user: dict = Depends(get_current_user)):
    """返回可用模板包列表（含当前选中）。"""
    templates = [
        {'name': template_id, 'current': template_id == config.image.template}
        for template_id in extension_manager.templates
    ]
    return {'code': 0, 'data': templates, 'message': 'ok'}


@router.post('/templates/switch', summary='切换模板')
async def switch_template(request: Request, user: dict = Depends(require_role('admin'))):
    """切换模板包并立即使模板缓存失效。"""
    try:
        body = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    template_name = (body or {}).get('name', '')
    if template_name not in extension_manager.templates:
        return {'code': 1, 'data': None, 'message': f'模板 {template_name} 不存在'}
    _patch_image_config('template', template_name)
    # 标准用法：直接使全部模板环境失效
    extension_manager.renderer_manager.invalidate_all()
    return {'code': 0, 'data': None, 'message': 'ok'}


def _patch_image_config(field_name: str, value: str) -> None:
    """将 image.<field> 写入 Config.toml 并热更新内存配置。"""
    config_manager.update_config({'image': {field_name: value}})
    reload_config()
