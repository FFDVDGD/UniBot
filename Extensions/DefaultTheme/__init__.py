"""
默认模板主题扩展。

提供内置图片模板（`templates/` 目录），经 Loader 主题注册机制挂载为
`theme_name = "default"` 主题，供 `Render.py` 加载模板时优先使用。
本扩展不声明任何能力类，模板目录由框架按约定（`<扩展目录>/templates`）注册。
"""

from Scripts.Extensions import Extension

# 唯一扩展实例，能力经实例装饰器登记；元数据以 Extension.toml 为准
extension = Extension(types=('render',))
