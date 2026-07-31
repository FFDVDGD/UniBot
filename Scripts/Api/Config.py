from copy import deepcopy

import tomlkit
from fastapi import APIRouter, Depends, Request

from Scripts.Config import TOML_PATH, Config, config
from Scripts.Managers import environment_manager
from .Auth import get_current_user, require_role
from .Constants import (
    ADAPTER_CATALOG,
    ENV_GROUPS,
    ENV_SCHEMA,
    PLATFORM_OPTIONS,
    PROTECTED_ADAPTER_MODULES,
    compute_redundant_drivers,
    deep_merge,
    format_driver,
    mask_api_key,
    merge_driver,
    shrink_driver,
)
from .Schemas import InstallAdapterRequest, NoneBotItemRequest, UninstallAdapterRequest

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
            'fields': [
                {'key': 'admin_superusers', 'label': '管理员视为超级用户', 'type': 'boolean', 'default': True, 'description': '是否将所有管理员视为超级用户'},
                {'key': 'qq_bound_max_number', 'label': 'QQ 绑定数量上限', 'type': 'number', 'default': 1, 'description': '每名玩家最多可绑定的 QQ 号数量，设置为 0 表示不限制'},
                {'key': 'command_groups', 'label': '指令群', 'type': 'platform_list', 'default': [], 'options': PLATFORM_OPTIONS, 'description': '机器人只响应这些平台群组内发送的指令'},
                {'key': 'message_groups', 'label': '消息群', 'type': 'platform_list', 'default': [], 'options': PLATFORM_OPTIONS, 'description': '接收游戏消息，并可向游戏内同步群消息的群'},
                {'key': 'command_minecraft_whitelist', 'label': '指令白名单', 'type': 'list', 'default': [], 'description': 'Command 指令只允许执行以列表内容开头的 Minecraft 指令；使用时请留空黑名单'},
                {'key': 'command_minecraft_blacklist', 'label': '指令黑名单', 'type': 'list', 'default': [], 'description': 'Command 指令禁止执行以列表内容开头的 Minecraft 指令'},
                {'key': 'broadcast_server', 'label': '播报服务器状态', 'type': 'boolean', 'default': True, 'description': '是否向其他服务器和消息群播报服务器开启或关闭'},
                {'key': 'broadcast_player', 'label': '播报玩家进出', 'type': 'boolean', 'default': True, 'description': '是否播报玩家进入或离开服务器'},
                {'key': 'sync_all_qq_message', 'label': '同步全部群消息', 'type': 'boolean', 'default': True, 'description': '是否将消息群内的所有消息转发到服务器；关闭后可使用 send 指令发送消息'},
                {'key': 'sync_all_game_message', 'label': '同步全部游戏消息', 'type': 'boolean', 'default': False, 'description': '是否将服务器内发送的所有消息转发到消息群'},
                {'key': 'sync_message_between_servers', 'label': '服务器间同步消息', 'type': 'boolean', 'default': False, 'description': '是否将服务器内的消息转发到其他服务器'},
                {'key': 'sync_sensitive_words', 'label': '同步敏感词', 'type': 'list', 'default': [], 'description': '包含列表中任意敏感词的消息不会同步到消息群，而会提示消息违禁'},
                {'key': 'sync_color_source', 'label': '消息来源颜色', 'type': 'string', 'default': 'gray', 'description': '群消息和跨服消息转发时，消息来源部分使用的 Minecraft 颜色'},
                {'key': 'sync_color_player', 'label': '玩家名称颜色', 'type': 'string', 'default': 'gray', 'description': '群消息和跨服消息转发时，玩家名称部分使用的 Minecraft 颜色'},
                {'key': 'sync_color_message', 'label': '消息内容颜色', 'type': 'string', 'default': 'gray', 'description': '群消息和跨服消息转发时，消息内容部分使用的 Minecraft 颜色'},
                {'key': 'bot_prefix', 'label': '假人前缀', 'type': 'string', 'default': '', 'description': 'list 指令分类和进服广播判定使用的假人名称前缀；无需分类时留空'},
                {'key': 'list_compatible_mode', 'label': '玩家列表兼容模式', 'type': 'boolean', 'default': False, 'description': '通过监听玩家进入和离开更新玩家列表，适用于无法直接获取列表的服务器，但数据可能不准确'},
                {'key': 'whitelist_command', 'label': '白名单指令名称', 'type': 'string', 'default': 'whitelist', 'description': '服务器用于管理白名单的 Minecraft 指令名称'},
                {'key': 'image.mode', 'label': '启用图片模式', 'type': 'boolean', 'default': False, 'description': '将机器人发送的消息渲染为图片；需要额外安装图片依赖，且响应速度会变慢'},
                {'key': 'image.background', 'label': '图片背景', 'type': 'string', 'default': '', 'description': '生成图片时使用的 CSS background-image 属性值'},
                {'key': 'ai.enabled', 'label': '启用 AI', 'type': 'boolean', 'default': False, 'description': '是否启用 AI 功能'},
                {'key': 'ai.base_url', 'label': 'API 基础地址', 'type': 'string', 'default': '', 'description': 'OpenAI 兼容接口的 Base URL；启用 AI 时必填'},
                {'key': 'ai.model_name', 'label': '模型名称', 'type': 'string', 'default': '', 'description': 'AI 请求使用的模型名称'},
                {'key': 'ai.api_key', 'label': 'API 密钥', 'type': 'secret', 'default': '', 'description': 'OpenAI 兼容接口的 API Key；启用 AI 时必填'},
                {'key': 'ai.system_prompt', 'label': '系统提示词', 'type': 'text', 'default': '', 'description': '描述 AI 的基本信息、身份与回复方式'},
                {'key': 'auto_reply.enabled', 'label': '启用自动回复', 'type': 'boolean', 'default': False, 'description': '是否启用关键词自动回复功能'},
                {'key': 'auto_reply.keywords', 'label': '关键词回复规则', 'type': 'keyword_map', 'default': {}, 'description': '为每条回复配置关键词；逗号分隔表示匹配任意关键词，空格分隔表示需要同时匹配'},
                {'key': 'webui.enabled', 'label': '启用 WebUI', 'type': 'boolean', 'default': False, 'description': '是否启用 WebUI 管理面板，并在机器人端口挂载 Web API 与 WebSocket'},
            ],
            'groups': [
                {'name': '基础与权限', 'keys': ['admin_superusers', 'qq_bound_max_number']},
                {'name': '群组', 'keys': ['command_groups', 'message_groups']},
                {'name': 'Minecraft 指令', 'keys': ['command_minecraft_whitelist', 'command_minecraft_blacklist']},
                {'name': '消息播报', 'keys': ['broadcast_server', 'broadcast_player']},
                {'name': '消息同步', 'keys': ['sync_all_qq_message', 'sync_all_game_message', 'sync_message_between_servers', 'sync_sensitive_words', 'sync_color_source', 'sync_color_player', 'sync_color_message']},
                {'name': '玩家列表', 'keys': ['bot_prefix', 'list_compatible_mode', 'whitelist_command']},
                {'name': '图片渲染', 'keys': ['image.mode', 'image.background']},
                {'name': 'AI', 'keys': ['ai.enabled', 'ai.base_url', 'ai.model_name', 'ai.api_key', 'ai.system_prompt']},
                {'name': '自动回复', 'keys': ['auto_reply.enabled', 'auto_reply.keywords']},
                {'name': 'WebUI', 'keys': ['webui.enabled']},
            ],
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
