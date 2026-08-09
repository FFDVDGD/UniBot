"""配置相关的纯函数工具。"""

from copy import deepcopy


def deep_merge(base: dict, override: dict) -> dict:
    """递归深合并两个字典，override 中的值覆盖 base。"""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
            continue
        result[key] = deepcopy(value)
    return result


def mask_api_key(data: dict) -> dict:
    """对 ai.api_key 进行脱敏处理。"""
    result = deepcopy(data)
    ai_config = result.get('ai', {})
    api_key = ai_config.get('api_key', '')
    if api_key:
        ai_config['api_key'] = api_key[:4] + '****'
    return result
