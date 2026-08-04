# 适配器

适配器（Adapter）是 UniBot 与各聊天平台之间的桥梁，负责将机器人账号连接到对应平台，是机器人与外部平台对接的通道。

UniBot 基于 **NoneBot2** 框架，通过安装不同的 **NoneBot 适配器** 来接入不同平台。每个平台对应一个独立的适配器，在 `.env` 中配置各自的接入字段。

## 支持的平台

| 平台 | 适配器 | 说明 |
|------|--------|------|
| **QQ** | OneBot V11 | 需配合 Lagrange.OneBot / NapCat / LLOneBot 等协议端 |
| **QQ 官方** | QQ 官方机器人 | 通过 QQ 开放平台接入 |
| **Telegram** | Telegram | 官方 Bot API |
| **Discord** | Discord | 官方 Bot |
| **DoDo** | DoDo | 开放平台接入 |
| **KOOK（开黑啦）** | KOOK | 开发者平台接入 |
| **Satori** | Satori | 通用协议，可对接 Chronocat 等 |
| **Minecraft** | Minecraft | 通过鹊桥协议与服务器互通 |

## 快速导航

- [接入聊天平台](/adapter/platforms.html) — 各平台适配器的配置字段与对接方式
- [Minecraft 适配器](/adapter/使用说明.html) — MC 协议适配器的配置与服务器对接

## Minecraft 适配器

**NoneBot-Adapter-Minecraft** 是 NoneBot 的 Minecraft 协议适配器，为 UniBot 提供与 Minecraft 服务器通信的能力，是 UniBot 与服务器之间的桥梁。

它通过 [鹊桥](/queqiao/) 协议，与服务器端的插件（如 [鹊桥 MCDR 端插件](/queqiao/mcdr.html)）互通。

## 相关项目

| 项目 | 说明 |
|------|------|
| [鹊桥](/queqiao/) | 服务器端插件/Mod，协议官方实现 |
| [QueQiao.MCDReforged](/queqiao/mcdr.html) | MCDR 端协议实现 |
| [nonebot-plugin-mcqq](https://github.com/17TheWord/nonebot-plugin-mcqq) | 更完善的 MC 通信插件 |
| [nonebot-plugin-mcping](https://github.com/17TheWord/nonebot-plugin-mcping) | 获取 MC 服务器 MOTD 并返回图片 |

## 开源许可

本项目使用 [MIT](https://github.com/17TheWord/nonebot-adapter-minecraft) 许可证。