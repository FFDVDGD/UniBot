'''配置相关的 FastAPI 路由。

负责 `Config.toml`、`.env`、`pyproject.toml`（NoneBot 适配器/插件）的读写接口。
'''

from copy import deepcopy

import tomlkit
from fastapi import APIRouter, Depends, Request

from Scripts.Config import TOML_PATH, Config, config
from Scripts.Managers import environment_manager
from ..Auth import get_current_user, require_role
from .Schema import CONFIG_GROUPS, CONFIG_SCHEMA, ENV_GROUPS, ENV_SCHEMA
from .Helpers import deep_merge, mask_api_key
from .Driver import compute_redundant_drivers, format_driver, merge_driver, shrink_driver
from .Adapters import ADAPTER_CATALOG, PROTECTED_ADAPTER_MODULES
from ..Schemas import InstallAdapterRequest, NoneBotItemRequest, UninstallAdapterRequest

router = APIRouter(prefix='/api/config', tags=['Config'])


@router.get('', summary='获取配置')
async def get_config(current_user: dict = Depends(get_current_user)):
    '''获取完整配置（api_key 脱敏）'''
    config_data = config.model_dump()
    return {
        'code': 0,
        'data': mask_api_key(config_data),
        'message': 'ok',
    }


@router.get('/schema', summary='获取配置 Schema')
async def get_config_schema(current_user: dict = Depends(get_current_user)):
    '''获取配置的 JSON Schema，供前端动态渲染表单'''
    return {
        'code': 0,
        'data': {
            'fields': CONFIG_SCHEMA,
            'groups': CONFIG_GROUPS,
        },
        'message': 'ok',
    }


@router.patch('', summary='更新配置')
async def patch_config(request: Request, current_user: dict = Depends(require_role('admin'))):
    '''部分更新配置，深合并后写回 Config.toml 并热更新'''
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}

    current_data = config.model_dump()
    merged_data = deep_merge(current_data, patch_data)

    # 写回 TOML 文件
    toml_output = deepcopy(merged_data)
    # 移除 NoneBot 内置配置字段（这些在 .env 中管理）
    for key in ('port', 'superusers', 'command_start'):
        toml_output.pop(key, None)

    # tomlkit 不支持 None 值，替换为空字符串
    def sanitize_none(data: dict) -> dict:
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = ''
            elif isinstance(value, dict):
                result[key] = sanitize_none(value)
            else:
                result[key] = value
        return result

    try:
        # 读取现有文件以保留注释和格式
        try:
            with open(TOML_PATH, 'r', encoding='utf-8') as file:
                toml_document = tomlkit.parse(file.read())
        except FileNotFoundError:
            toml_document = tomlkit.document()

        # 逐键更新，保留原有注释
        sanitized = sanitize_none(toml_output)
        for key, value in sanitized.items():
            if isinstance(value, dict) and key in toml_document and isinstance(toml_document[key], dict):
                for sub_key, sub_value in value.items():
                    toml_document[key][sub_key] = sub_value
            else:
                toml_document[key] = value

        with open(TOML_PATH, 'w', encoding='utf-8') as file:
            file.write(tomlkit.dumps(toml_document))
    except Exception as error:
        return {'code': 500, 'data': None, 'message': f'写入配置文件失败：{error}'}

    # 热更新内存中的配置对象（先经模型校验，保证嵌套配置仍为 Pydantic 子模型而非 dict）
    updated_config = Config.model_validate(merged_data)
    for field_name in Config.model_fields:
        setattr(config, field_name, getattr(updated_config, field_name))

    return {'code': 0, 'data': None, 'message': 'ok'}


# ===== .env 环境变量配置 =====


@router.get('/env', summary='获取环境变量配置')
async def get_env_config(current_user: dict = Depends(get_current_user)):
    '''获取 .env 中的配置项'''
    return {
        'code': 0,
        'data': {
            'values': environment_manager.read_env(),
            'schema': ENV_SCHEMA,
            'groups': ENV_GROUPS,
        },
        'message': 'ok',
    }


@router.patch('/env', summary='更新环境变量配置')
async def patch_env_config(request: Request, current_user: dict = Depends(require_role('admin'))):
    '''部分更新 .env 配置，写回文件（需重启生效）'''
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    environment_manager.update_env(patch_data)
    return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}


# ===== pyproject.toml NoneBot 插件/适配器管理 =====


@router.get('/nonebot', summary='获取 NoneBot 插件与适配器列表')
async def get_nonebot_config(current_user: dict = Depends(get_current_user)):
    '''获取 pyproject.toml 中的 NoneBot 适配器和插件配置'''
    project_data = environment_manager.read_pyproject()
    nonebot_section = project_data.get('tool', {}).get('nonebot', {})
    adapters = [
        {**adapter, 'removable': adapter.get('module_name') not in PROTECTED_ADAPTER_MODULES}
        for adapter in nonebot_section.get('adapters', [])
        if isinstance(adapter, dict)
    ]
    registered_modules = {
        adapter.get('module_name') for adapter in adapters
    }
    installed_packages = {
        dep.split('[')[0].split('>=')[0].split('<')[0].split('~')[0].split('!=')[0].strip()
        for dep in project_data.get('project', {}).get('dependencies', [])
    }
    catalog = [
        {
            **adapter,
            'registered': adapter['module_name'] in registered_modules,
            'installed': adapter['package'] in installed_packages,
            'removable': adapter['module_name'] not in PROTECTED_ADAPTER_MODULES,
        }
        for adapter in ADAPTER_CATALOG
    ]
    return {
        'code': 0,
        'data': {
            'adapters': adapters,
            'plugins': nonebot_section.get('plugins', []),
            'adapter_catalog': catalog,
        },
        'message': 'ok',
    }


@router.post('/nonebot/adapters/install', summary='安装并注册适配器')
async def install_adapter(body: InstallAdapterRequest, current_user: dict = Depends(require_role('admin'))):
    '''向 pyproject.toml 写入依赖记录和 NoneBot 适配器配置，并自动补全所需驱动。'''
    adapter = next((item for item in ADAPTER_CATALOG if item['id'] == body.adapter_id), None)
    if adapter is None:
        return {'code': 404, 'data': None, 'message': '适配器不在内置目录中'}
    environment_manager.add_dependency(adapter['package'])
    environment_manager.add_adapter(adapter['name'], adapter['module_name'])
    new_driver, added_drivers = merge_driver(adapter.get('drivers', []))
    message = '依赖和注册信息已写入（重启时自动同步）'
    if added_drivers:
        message += f'；已自动追加驱动：{format_driver(added_drivers)}（当前 DRIVER={new_driver}）'
    return {'code': 0, 'data': adapter, 'message': message}


@router.post('/nonebot/adapters', summary='添加适配器')
async def add_adapter(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''向 pyproject.toml 添加适配器'''
    if environment_manager.add_adapter(body.name, body.module_name):
        return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
    return {'code': 1, 'data': None, 'message': '该适配器已存在'}


@router.delete('/nonebot/adapters', summary='移除适配器注册')
async def remove_adapter(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''从 pyproject.toml 移除适配器注册（不删除依赖包）'''
    if body.module_name in PROTECTED_ADAPTER_MODULES:
        return {'code': 1, 'data': None, 'message': 'Minecraft 适配器是 UniBot 核心依赖，禁止卸载'}
    environment_manager.remove_adapter(body.module_name)
    return {'code': 0, 'data': None, 'message': '适配器已禁用（重启后生效）'}


@router.delete('/nonebot/adapters/uninstall', summary='彻底卸载适配器')
async def uninstall_adapter(body: UninstallAdapterRequest, current_user: dict = Depends(require_role('admin'))):
    '''从 pyproject.toml 移除适配器注册和依赖记录，并清理多余驱动。'''
    if body.module_name in PROTECTED_ADAPTER_MODULES:
        return {'code': 1, 'data': None, 'message': 'Minecraft 适配器是 UniBot 核心依赖，禁止卸载'}
    adapter = next(
        (item for item in ADAPTER_CATALOG if item['module_name'] == body.module_name),
        None,
    )
    if adapter is None:
        return {'code': 1, 'data': None, 'message': '该适配器不在内置目录中，无法安全卸载依赖'}
    environment_manager.remove_adapter(body.module_name)
    environment_manager.remove_dependency(adapter['package'])
    redundant = compute_redundant_drivers(body.module_name)
    new_driver, removed_drivers = shrink_driver(redundant)
    message = '适配器及其依赖记录已删除（重启时自动同步）'
    if removed_drivers:
        message += f'；已自动移除多余驱动：{format_driver(removed_drivers)}（当前 DRIVER={new_driver}）'
    return {'code': 0, 'data': None, 'message': message}


@router.post('/nonebot/plugins', summary='添加插件')
async def add_plugin(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''向 pyproject.toml 添加插件'''
    if environment_manager.add_plugin(body.module_name):
        return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
    return {'code': 1, 'data': None, 'message': '该插件已存在'}


@router.delete('/nonebot/plugins', summary='移除插件')
async def remove_plugin(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''从 pyproject.toml 移除插件'''
    if body.module_name.startswith('Plugins.'):
        return {'code': 1, 'data': None, 'message': '内置插件不允许删除'}
    environment_manager.remove_plugin(body.module_name)
    return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
