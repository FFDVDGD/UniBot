# 鹊桥

「鹊桥」是一套由 [17TheWord / QueQiao](https://github.com/17TheWord/QueQiao) 开发的 **第三方通信协议**，负责打通 Minecraft 服务器与外部聊天系统（如 UniBot）。

服务器端需安装 **鹊桥的实现端** 才能接入机器人。根据服务端类型不同，实现方式分为两类：

## 接入方式

::: table title="接入方式" copy="all" hl-rows="tip:2"
| 服务端类型 | 实现端 | 说明 |
|------------|--------|------|
| MCDReforged | [MCDR 端插件](/queqiao/mcdr.html) | 本项目维护实现 |
| Spigot / Paper / Folia / Forge / Fabric / NeoForge / Velocity / 原版 | [鹊桥官方实现](/queqiao/official.html) | 第三方官方实现 |
:::

*需说明的是：本项目仅维护其中的 MCDR 端插件。* 鹊桥协议本身并非本项目开发，它还支持 Spigot、Paper、Fabric、Forge、NeoForge 等多种服务端。

## 快速导航

<LinkCard title="MCDR 端插件" href="/queqiao/mcdr.html" icon="fluent-color:toolbox-24">

本项目维护的 MCDR 实现，安装、配置与命令。

</LinkCard>

<LinkCard title="鹊桥官方实现" href="/queqiao/official.html" icon="fluent-color:globe-24">

其它服务端的官方实现，安装、配置与对接。

</LinkCard>

## 协议概述

鹊桥 V2 协议基于 WebSocket，通过 `Authorization` 头鉴权，双向实时通信。服务端将游戏事件（玩家进出、聊天、死亡、成就等）转发给外部客户端，同时接收外部客户端发送的 API 指令（广播、私聊、Title、ActionBar、RCON 等）。

## 对接项目

鹊桥协议已有多套对接实现，UniBot 通过 [nonebot-adapter-minecraft](/adapter/使用说明.html) 接入：

::: table title="对接项目" copy="all"
| 项目 | 说明 |
|------|------|
| [nonebot-adapter-minecraft](/adapter/) | NoneBot 的 Minecraft 适配器，UniBot 使用 |
| [nonebot-plugin-mcqq](https://github.com/17TheWord/nonebot-plugin-mcqq) | 更完善的 MC 通信插件 |
| [nonebot-plugin-mcping](https://github.com/17TheWord/nonebot-plugin-mcping) | 获取 MC 服务器 MOTD 并返回图片 |
:::