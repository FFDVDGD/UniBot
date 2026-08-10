"""默认主题扩展测试：Loader 主题目录注册（[render] kind 含 theme 的扩展）。"""

from Scripts.Extensions import Extension, extension_manager
from Scripts.Extensions.Base import ExtensionMetadata, parse_manifest
from Scripts.Extensions.Loader import ExtensionLoader

_TEMPLATE_TOML = """
[manifest]
schema_version = 1

[extension]
id = "DefaultTheme"
name = "默认模板主题"
version = "1.0.0"
author = "UniBot"
description = "默认模板"
types = ["render"]

[render]
kind = ["theme"]
theme_name = "{theme_name}"
"""


def _make_extension(theme_name: str = 'default') -> Extension:
    """构造一个仅声明 render_kind=['theme'] 的扩展实例。"""
    manifest = parse_manifest(_TEMPLATE_TOML.format(theme_name=theme_name))
    extension = Extension(types=('render',))
    extension._set_metadata(ExtensionMetadata(manifest))
    return extension


class TestLoaderThemeRegistration:
    def test_commit_renderers_registers_theme_directory(self, tmp_path):
        templates_dir = tmp_path / 'Templates'
        templates_dir.mkdir()
        loader = ExtensionLoader(extension_manager)
        loader._commit_renderers(_make_extension(), tmp_path)
        assert extension_manager.themes.get('default') == templates_dir

    def test_theme_key_falls_back_to_extension_id(self, tmp_path):
        (tmp_path / 'Templates').mkdir()
        loader = ExtensionLoader(extension_manager)
        loader._commit_renderers(_make_extension(theme_name=''), tmp_path)
        assert extension_manager.themes.get('DefaultTheme') == tmp_path / 'Templates'

    def test_missing_templates_dir_is_ignored(self, tmp_path):
        # 无 Templates 目录时不应注册任何主题，也不抛异常
        loader = ExtensionLoader(extension_manager)
        loader._commit_renderers(_make_extension(), tmp_path)
        assert extension_manager.themes == {}

    def test_non_theme_extension_registers_no_theme(self, tmp_path):
        (tmp_path / 'Templates').mkdir()
        manifest = parse_manifest(
            _TEMPLATE_TOML.format(theme_name='').replace(
                'kind = ["theme"]', 'kind = ["engine"]'
            )
        )
        extension = Extension(types=('render',))
        extension._set_metadata(ExtensionMetadata(manifest))
        loader = ExtensionLoader(extension_manager)
        loader._commit_renderers(extension, tmp_path)
        assert extension_manager.themes == {}
