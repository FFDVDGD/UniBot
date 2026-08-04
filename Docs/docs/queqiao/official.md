# 鹊桥官方实现

除本项目维护的 [MCDR 端插件](/queqiao/mcdr.html) 外，鹊桥还提供了适用于其它服务端的官方实现，支持 **Spigot / Paper / Folia / Forge / Fabric / NeoForge / Velocity / 原版** 等。

*需说明的是：以下内容为鹊桥官方实现的使用与配置，并非本项目开发。* 完整文档请参阅 [鹊桥官方文档](https://queqiao-docs.pages.dev)。

## 支持的服务端

| 类型 | 说明 | 版本范围 |
|------|------|----------|
| Spigot / Paper / Folia | Bukkit 系插件 | 1.12.2 起 |
| Forge / NeoForge | Mod 加载器 | 1.7.10 起 |
| Fabric | Mod 加载器 | 1.16.5 起 |
| Velocity | 代理端插件 | 3.3.0 |
| 原版 | 独立程序（独立运行） | 原版 |

## 安装

从 [Modrinth](https://modrinth.com/plugin/queqiao) 或 [CurseForge](https://www.curseforge.com/minecraft/mc-mods/queqiao) 下载 **对应服务端类型** 的插件 / Mod，放入服务端对应目录后启动即可。

*插件端与模组端的配置文件路径不同。* 插件端位于 `./plugins/QueQiao/config.yml`，模组端位于 `./config/QueQiao/config.yml`。

## 配置

`config.yml` 核心配置如下：

```yaml
enable: true # 是否启用插件/模组

server_name: "Server" # 服务器名称，多个服务器时使用不同命名
access_token: ""      # 连接时验证用，无需 Bearer 前缀，留空则不验证

# 消息前缀（不含 Title、ActionBar），为空则不添加
message_prefix: "[鹊桥]"

# 是否启用消息翻译（成就、死亡等翻译键转本地化文本）
enable_translation: false

# WebSocket Server 配置项（正向 WebSocket）
websocket_server:
  enable: true          # 是否启用
  host: "127.0.0.1"     # WebSocket Server 地址
  port: 8080            # WebSocket Server 端口

# WebSocket Client 配置项（反向 WebSocket）
websocket_client:
  enable: false                 # 是否启用
  reconnect_interval: 5         # 重连间隔（秒）
  reconnect_max_times: 5        # 最大重连次数
  url_list:
    - "ws://127.0.0.1:8080/minecraft/ws"

# Rcon 客户端配置项
rcon:
  enable: false          # 是否启用
  port: 25575            # Rcon 端口
  password: ""           # Rcon 密码

# 订阅事件配置项
subscribe_event:
  player_chat: true         # 玩家聊天
  player_death: true        # 玩家死亡
  player_join: true         # 玩家加入
  player_quit: true         # 玩家退出
  player_command: true      # 玩家命令
  player_advancement: true  # 玩家成就

# 忽略的命令列表，如 ["tp"] 则所有以 /tp 起始的命令事件不被广播
ignored_commands: []
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `enable` | 是否启用插件 / 模组 |
| `server_name` | 服务器名称，用于 Header `x-self-name` 与事件标识 |
| `access_token` | 鉴权 Token，留空则不验证 |
| `message_prefix` | 消息前缀，支持 MC 文本组件 JSON |
| `enable_translation` | 是否启用翻译功能 |
| `websocket_server` | 正向 WebSocket 服务端配置 |
| `websocket_client` | 反向 WebSocket 客户端配置 |
| `rcon` | RCON 客户端配置 |
| `subscribe_event` | 订阅事件开关 |
| `ignored_commands` | 忽略的命令列表 |

### 翻译功能（可选）

启用 `enable_translation: true` 后，还需在 `config.yml` 同级目录下创建 `translate` 文件夹（插件端 `./plugins/QueQiao/translate/`，模组端 `./config/QueQiao/translate/`），放入 JSON 语言文件（如从客户端 jar 包提取的 `zh_cn.json`）。该功能可将成就、死亡事件中的翻译键转换为本地化文本。

## 连接模式

鹊桥提供 **正向 WebSocket** 与 **反向 WebSocket** 两种连接方式，任选其一即可。

### 正向 WebSocket（服务端模式）

在 `websocket_server` 中启用并监听地址 / 端口，服务端等待客户端接入。适用于服务端能对外暴露端口、由适配器主动连接的场景。

### 反向 WebSocket（客户端模式）

在 `websocket_client` 中启用，并在 `url_list` 中填写对端 WebSocket 地址。服务端主动外连，适用于服务端在内网、无法暴露端口的场景。

## Header 鉴权

使用任一连接方式时，均需携带或校验以下 Header：

| Header | 必填 | 说明 |
|--------|------|------|
| `x-self-name` | ✅ | 服务器名称，必须与 `config.yml` 的 `server_name` 一致 |
| `Authorization` | ⚠️ | 鉴权，`Bearer <access_token>`，`access_token` 为空时可省略 |
| `x-client-origin` | ⚠️ | 对接项目来源标记，如 `minecraft` / `nonebot`，建议填写 |

## 游戏内命令

| 命令 | 权限节点 | 说明 |
|------|----------|------|
| `/queqiao help` | `queqiao.help` | 显示帮助 |
| `/queqiao reload` | `queqiao.reload` | 重载配置并重启 WebSocket |
| `/queqiao client reconnect [all]` | `queqiao.client.reconnect` | 重连 WebSocket Client（`all` 强制全部重连） |

*Mod 端对权限的判定为 int Level，本模组所有命令权限定义为 `2`。*

## 与适配器对接

UniBot 通过 [nonebot-adapter-minecraft](/adapter/使用说明.html) 与鹊桥官方实现互通。两者在 `x-self-name`、`Authorization` 上保持一致即可建立连接，具体对接方式见 [适配器使用说明](/adapter/使用说明.html#与服务器对接)。