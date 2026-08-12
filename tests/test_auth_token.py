"""认证令牌测试：初始化生成、即用即刷与授权写入逻辑。"""

from types import SimpleNamespace

from nonebot_plugin_uninfo import SceneType

from Scripts.Config import config
from Scripts.Managers import config_manager
from Scripts.Plugins.Token import (
    add_group,
    add_superuser,
    get_current_token,
    get_group_info,
    is_valid_token,
    normalize_token,
    refresh_token,
)

TOKEN_LENGTH = 10


def test_token_format_and_initial():
    """令牌为固定长度大写文本，初始化时已生成记录。"""
    token = get_current_token()
    assert len(token) == TOKEN_LENGTH
    assert token.isalnum() and token.isupper()


def test_normalize_token():
    """规范化：去除指令前缀与首尾空白。"""
    token = get_current_token()
    assert normalize_token(token) == token
    assert normalize_token(f'  .{token}  ') == token


def test_token_refresh_invalidates_old():
    """即用即刷：刷新后旧令牌立即作废，新令牌有效。"""
    old_token = get_current_token()
    assert is_valid_token(old_token)
    new_token = refresh_token()
    assert new_token != old_token
    assert not is_valid_token(old_token)
    assert is_valid_token(new_token)
    assert not is_valid_token('INVALIDTOKEN')


def _make_session(scene_type: SceneType, scene_id: str, user_id: str = '10001'):
    """构造带场景与用户信息的模拟会话。"""
    return SimpleNamespace(
        scope='QQClient',
        scene=SimpleNamespace(type=scene_type, id=scene_id),
        user=SimpleNamespace(id=user_id),
    )


def test_get_group_info():
    """群聊场景返回平台前缀的群信息，私聊场景返回 None。"""
    session = _make_session(SceneType.GROUP, '12345')
    assert get_group_info(session) == 'qq_client:12345'
    private = _make_session(SceneType.PRIVATE, '10001')
    assert get_group_info(private) is None


def test_add_group_and_superuser(monkeypatch):
    """授权写入：群加入指令群与消息群，用户加入超级用户，重复授权不重复写入。"""
    updates = []
    monkeypatch.setattr(config_manager, 'update_config', lambda data: updates.append(data))
    monkeypatch.setattr(config_manager, 'update_env', lambda data: updates.append(data))
    monkeypatch.setattr(config, 'command_groups', [])
    monkeypatch.setattr(config, 'message_groups', [])
    monkeypatch.setattr(config, 'superusers', [])

    session = _make_session(SceneType.GROUP, '12345', user_id='10001')
    assert add_group('qq_client:12345') == '已将本群加入 command_groups、message_groups'
    assert config.command_groups == ['qq_client:12345']
    assert config.message_groups == ['qq_client:12345']
    assert add_superuser(session) == '已将你设为超级用户'
    assert config.superusers == ['10001']

    assert add_group('qq_client:12345') == '本群已在授权列表中'
    assert add_superuser(session) == '你已是超级用户'
    assert updates == [
        {'command_groups': ['qq_client:12345']},
        {'message_groups': ['qq_client:12345']},
        {'SUPERUSERS': ['10001']},
    ]
