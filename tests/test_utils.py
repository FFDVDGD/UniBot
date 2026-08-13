"""通用工具函数测试。"""

from Scripts.Utils import strip_minecraft_color


class TestStripMinecraftColor:
    def test_single_color_codes(self):
        assert strip_minecraft_color('§6已运行时间：§c7 小时') == '已运行时间：7 小时'

    def test_uppercase_codes(self):
        assert strip_minecraft_color('§A测试§B文本') == '测试文本'

    def test_format_codes(self):
        assert strip_minecraft_color('§l加粗§o斜体§r重置') == '加粗斜体重置'

    def test_hex_color_sequence(self):
        assert strip_minecraft_color('§x§1§2§3§4§5§6测试') == '测试'

    def test_plain_text_unchanged(self):
        assert strip_minecraft_color('没有颜色的文本') == '没有颜色的文本'

    def test_empty_string(self):
        assert strip_minecraft_color('') == ''
