---
home: true
pageLayout: home
config:
  -
    type: doc-hero
    hero:
      name: Minecraft UniBot
      tagline: 跨平台 · 多服互联 · 即插即用
      text: 让 Minecraft 与你的聊天世界无缝相连
      image: /icon.svg
      actions:
        -
          theme: brand
          text: 快速开始
          link: /guide/快速开始.html
        -
          theme: alt
          text: 项目介绍
          link: /guide/
  -
    type: features
    features:
      -
        title: 🌐 真正的跨平台
        details: 不止 QQ，还支持 Telegram、Discord、Kook、QQ 频道等，一套指令全平台通用。
      -
        title: 🔗 多服互联
        details: 同时连接多台 Minecraft 服务器，消息互通，跨服聊天零延迟。
      -
        title: 🔄 全服务端兼容
        details: 支持 Fabric、Forge、Spigot、Paper 等主流服务端，即插即用，无需额外适配。
      -
        title: 🧩 模块化架构
        details: 指令按插件拆分，扩展新功能就像搭积木。
      -
        title: 🖥️ WebUI 管理面板
        details: 现代化管理界面，可视化配置、实时监控、日志查看，开箱即用。
      -
        title: 🤖 AI 智能对话
        details: 接入任意 OpenAI 兼容 API，@机器人即可与 AI 对话，支持上下文记忆。
      -
        title: 🔐 白名单管理
        details: 完善的平台账号与游戏 ID 绑定系统，支持多服白名单同步。
      -
        title: 🎨 图片渲染模式
        details: 基于 HTML + CSS 模板引擎，将指令输出渲染为精美图片，支持自定义背景。
  -
    type: custom
---

这是 **Minecraft UniBot** 项目的官方文档。本项目由多个子项目共同构成，目标是打造一套跨平台、多服互联的 Minecraft 机器人生态。

## 📚 项目组成

| 子项目 | 说明 | 技术栈 |
|--------|------|--------|
| [UniBot](/unibot/) | 主机器人框架，负责消息收发、指令处理与 WebUI 管理 | NoneBot2 / Python |
| [鹊桥](/queqiao/) | 第三方通信协议，本项目维护其 MCDR 端插件 | MCDReforged / Python |
| [MC 适配器](/adapter/) | NoneBot 的 Minecraft 协议适配器，为 UniBot 提供 MC 通信能力 | NoneBot Adapter |

> [!TIP]
> 本文档中的「鹊桥」指本项目维护的 **MCDReforged 端插件**。鹊桥协议本身由 [17TheWord / QueQiao](https://github.com/17TheWord/QueQiao) 官方维护，除此端外还支持 Spigot、Paper、Fabric、Forge、NeoForge、Vanilla、Folia、Velocity 等多种服务端，并非由本项目开发。

## 🚀 快速导航

- [开始使用](/guide/快速开始.html) — 从零开始部署你的 UniBot
- [配置说明](/guide/配置说明.html) — 双配置文件详解
- [指令手册](/guide/指令手册.html) — 全部内置指令一览
- [功能特性](/guide/功能特性.html) — 群服互通、图片渲染、AI 对话等
- [架构设计](/unibot/架构设计.html) — 深入了解项目架构
- [鹊桥](/queqiao/) — 第三方通信协议，本项目维护其 MCDR 端插件
