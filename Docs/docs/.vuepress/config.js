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
    // 部署域名：用于 SEO（OGP / JSON-LD / canonical）与 sitemap.xml 的生成
    hostname: 'https://bot.mcjpg.dev/',

    logo: '/icon.svg',
    repo: 'MineJPGcraft/UniBot',
    docsDir: 'Docs/docs',

    markdown: {
      // 流程图（已从 flowchart 切换到 mermaid，节点内可用 <br/> 换行）：```mermaid
      mermaid: true,
      // 旧版 flowchart 语法（已弃用，保留配置以防残留代码块）：```flow:preset
      // flowchart: true,
      // Markdown 内联图标：::fluent-color:name::
      icon: { provider: 'iconify' },
      // 表格增强：::: table（标题 / 复制 / 高亮）
      table: true,
      // 折叠面板：::: collapse
      collapse: true,
      // 缩写词语法：*[xxx]: 定义
      abbr: true,
    },

    social: [
      {
        icon: {
          svg: '<img src="https://mcjpg.org/logo.png" style="width:20px;height:20px;border-radius:50%;object-fit:cover;" />',
          name: 'mcjpg',
        },
        link: 'https://mcjpg.org/',
      },
      { icon: 'github', link: 'https://github.com/MineJPGcraft/UniBot' },
      { icon: 'qq', link: 'https://qm.qq.com/q/qyq2XH6qkw', ariaLabel: '加入 QQ 群' },
    ],

    navbarSocialInclude: ['github', 'mcjpg', 'qq'],

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
            '/guide/功能特性.md',
            '/guide/快速开始.md',
            '/guide/指令手册.md',
          ],
        },
      ],
      '/unibot/': [
        {
          text: 'UniBot',
          collapsed: false,
          items: [
            '/unibot/',
            '/unibot/配置说明.md',
            '/unibot/扩展系统.md',
            '/unibot/架构设计.md',
            '/unibot/接口文档.md',
            '/unibot/开发插件.md',
            '/unibot/上传市场.md',
          ],
        },
      ],
      '/queqiao/': [
        {
          text: '鹊桥',
          collapsed: false,
          items: [
            '/queqiao/',
            '/queqiao/MCDR端插件.md',
            '/queqiao/官方实现.md',
          ],
        },
      ],
      '/adapter/': [
        {
          text: 'MC 适配器',
          collapsed: false,
          items: [
            '/adapter/',
            '/adapter/接入聊天平台.md',
            '/adapter/使用说明.md',
          ],
        },
      ],
    },

    plugins: {
      // SEO：默认生成 OGP / JSON-LD / robots.txt，仅生产构建（vuepress build）生效
      seo: {
        // 站点默认作者（页面 frontmatter 中 author 优先）
        author: {
          name: 'McJPG 团队',
          url: 'https://mcjpg.org/',
        },
        // 无配图页面回退到站点图标（需绝对 URL）
        fallBackImage: 'https://bot.mcjpg.dev/icon.svg',
        // 补充默认 OGP：强制站点名（若站点新增语言后 siteData 取到其他 title 时兜底）
        ogp: (ogpInfo) => ({
          ...ogpInfo,
          'og:site_name': 'Minecraft UniBot',
        }),
      },
      // sitemap：生成 sitemap.xml（仅生产构建生效，hostname 自动继承顶层配置）
      sitemap: {},
    },
  }),

  bundler: viteBundler(),
})
