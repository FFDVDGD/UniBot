此目录是默认模板扩展（Default）自带的资源根目录。

模板可通过资源函数引用这里的文件：

- `resource_path('Default', 'path/to/file')` - 磁盘绝对路径
- `resource_url('Default', 'path/to/file')` - file:// URL
- `resource_text('Default', 'path/to/file')` - 文本内容
- `resource_bytes('Default', 'path/to/file')` - 字节内容
