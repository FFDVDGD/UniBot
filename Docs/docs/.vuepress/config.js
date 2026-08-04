import { defineUserConfig } from 'vuepress'
import { viteBundler } from '@vuepress/bundler-vite'
import { plumeTheme } from 'vuepress-theme-plume'

export default defineUserConfig({
  lang: 'zh-CN',
  title: 'Minecraft UniBot',
  description: '跨平台 · 多服互联 · 即插即用 —— 让 Minecraft 与你的聊天世界无缝相连',

  head: [
    ['link', { rel: 'icon', href: '/icon.svg' }],
  ],

  theme: plumeTheme({
    logo: '/icon.svg',
    repo: 'MineJPGcraft/UniBot',
    docsDir: 'Docs/docs',

    social: [
      { icon: 'github', link: 'https://github.com/MineJPGcraft/UniBot' },
    ],

    navbar: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/' },
      { text: 'UniBot', link: '/unibot/' },
      { text: '鹊桥', link: '/queqiao/' },
      { text: '适配器', link: '/adapter/' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: '指南',
          collapsed: false,
          items: [
            '/guide/',
            '/guide/快速开始.md',
            '/guide/配置说明.md',
            '/guide/指令手册.md',
            '/guide/功能特性.md',
          ],
        },
      ],
      '/unibot/': [
        {
          text: 'UniBot',
          collapsed: false,
          items: [
            '/unibot/',
            '/unibot/架构设计.md',
            '/unibot/接口文档.md',
          ],
        },
      ],
      '/queqiao/': [
        {
          text: '鹊桥',
          collapsed: false,
          items: [
            '/queqiao/',
            '/queqiao/mcdr.md',
            '/queqiao/official.md',
          ],
        },
      ],
      '/adapter/': [
        {
          text: 'MC 适配器',
          collapsed: false,
          items: [
            '/adapter/',
            '/adapter/platforms.md',
            '/adapter/使用说明.md',
          ],
        },
      ],
    },
  }),

  bundler: viteBundler(),
})
