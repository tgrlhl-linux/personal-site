# guorui-site

个人网站 · [shengxia.dev](https://shengxia.dev)

记录项目、笔记与生活爱好。基于 Astro 构建，暖色调设计。

## 技术栈

- **框架**：Astro 5
- **内容**：Markdown + Astro Content Collections
- **部署**：Vercel
- **域名**：shengxia.dev

## 本地开发

```bash
npm install
npm run dev      # 启动开发服务器
npm run build    # 构建静态输出
npm run preview  # 预览构建结果
```

## 站点结构

```
src/
├── content/        # 内容文件（Markdown）
│   ├── projects/   # 项目
│   ├── notes/      # 笔记
│   └── hobbies/    # 爱好
├── components/     # A stro 组件
├── layouts/        # 页面布局
├── pages/          # 页面路由
└── styles/         # 全局样式
```

## License

MIT
