/**
 * 成长里程碑数据
 *
 * 记录我的成长历程中的关键节点。
 * 日期格式：'YYYY-MM-DD'，已知精确日期用真实日期，
 * 课程项目使用估计日期（标注 ~）。
 *
 * category 分类:
 *   web      — 网站开发（蓝 #58a6ff）
 *   project  — 课程项目（绿 #3fb950）
 *   academic — 学业（琥珀 #d29922）
 *   life     — 生活/其他（紫 #bc8cff）
 */

export const milestones = [
  // ═══════════════════════════════════
  // 2026 年 7 月 — 个人网站
  // ═══════════════════════════════════
  {
    date: '2026-07-16',
    title: '个人网站项目初始化',
    desc: '从零搭建 Astro 5 个人成长网站，配置域名 shengxia.dev，Vercel 自动部署上线',
    category: 'web',
  },
  {
    date: '2026-07-17',
    title: 'SSR + 数据库 + 管理后台',
    desc: '架构升级为 SSR 模式，接入 TiDB Cloud，搭建笔记 CRUD 管理后台',
    category: 'web',
  },
  {
    date: '2026-07-18',
    title: '暗色霓虹 v2 重构',
    desc: '全站重构为统一内容引擎 + Bento Grid 布局 + 暗色霓虹配色体系',
    category: 'web',
  },
  {
    date: '2026-07-18',
    title: '项目代码展示系统上线',
    desc: '12 个项目完整源码整合入库，语法高亮 + 四标签页，10 篇技术分析报告',
    category: 'web',
  },
  {
    date: '2026-07-18',
    title: 'MiniSQL 在线 SQL 执行器',
    desc: '浏览器内 SQL 引擎，Unity 暗色主题 IDE 风格交互演示',
    category: 'web',
  },
  {
    date: '2026-07-20',
    title: '全站优化 v4 — 动画/安全/SEO',
    desc: '移除 GSAP+Three.js CDN（-750KB），HMAC 安全认证，OG+Twitter+JSON-LD SEO 体系',
    category: 'web',
  },
  {
    date: '2026-07-20',
    title: '期末复习笔记入库',
    desc: '操作系统 / 数据库原理 / 概率论 / 思政 四门课 25 篇复习笔记录入数据库',
    category: 'academic',
  },
  {
    date: '2026-07-20',
    title: '暗亮色模式',
    desc: '完整暗亮主题系统（FOUC 防护 + 系统偏好检测）',
    category: 'web',
  },
  {
    date: '2026-07-21',
    title: '笔记补全 + 编辑器体验优化',
    desc: '29 篇笔记全部入库，编辑器自动保存草稿，搜索关键词高亮 + 输入即搜',
    category: 'web',
  },
  {
    date: '2026-07-21',
    title: '成长时间线上线',
    desc: 'GitHub 风格贡献热力图 + 里程碑时间线，记录成长历程',
    category: 'web',
  },

  // ═══════════════════════════════════
  // 2026 年 — 课程项目（大三下 ~3月-6月）
  // ═══════════════════════════════════
  {
    date: '2026-03-15',
    title: '~ Linux Shell 成绩管理系统',
    desc: 'Bash 脚本实现学生成绩增删改查，支持多用户数据隔离和批量导入',
    category: 'project',
  },
  {
    date: '2026-04-01',
    title: '~ MiniSQL — Java SQL 引擎',
    desc: '从零实现 SQL 词法分析、语法分析（LL(1)）、查询执行引擎，零外部依赖',
    category: 'project',
  },
  {
    date: '2026-04-10',
    title: '~ OS 实验1：进程调度仿真',
    desc: 'C 语言实现时间片轮转/优先数调度算法，可视化甘特图对比',
    category: 'project',
  },
  {
    date: '2026-04-20',
    title: '~ OS 实验2：虚拟内存管理',
    desc: 'FIFO/LRU/OPT 页面置换算法仿真，缺页率对比分析',
    category: 'project',
  },
  {
    date: '2026-05-01',
    title: '~ HDFS 客户端',
    desc: 'Java Hadoop HDFS API，文件上传下载，副本优先级测试',
    category: 'project',
  },
  {
    date: '2026-05-10',
    title: '~ 沉浸式剧本平台（数据库大作业）',
    desc: '完整数据库设计：E-R → 关系模式 → SQL 表结构 + 触发器 + 视图 + 存储过程',
    category: 'project',
  },
  {
    date: '2026-05-15',
    title: '~ OS 实验3：磁盘调度算法',
    desc: 'FCFS/SSTF/SCAN/C-SCAN 四算法仿真，磁道访问序列对比',
    category: 'project',
  },
  {
    date: '2026-05-20',
    title: '~ 叙事分析系统',
    desc: 'Hadoop MapReduce 分析 17 部电影剧本，情感曲线 + 角色共现网络',
    category: 'project',
  },
  {
    date: '2026-06-01',
    title: '~ OS 实验4：文件系统仿真（Rust）',
    desc: 'Rust + egui 实现位图磁盘管理，文件分配/回收可视化，点击交互',
    category: 'project',
  },
  {
    date: '2026-06-10',
    title: '~ Flask 成绩管理系统',
    desc: 'Flask Web 应用 + 624 条真实数据，Vercel Serverless 部署',
    category: 'project',
  },
  {
    date: '2026-06-15',
    title: '~ Cosmic 3D 星空可视化',
    desc: 'Three.js 4000 粒子星空 + 星轨系统，交互式 3D 可视化',
    category: 'project',
  },
  {
    date: '2026-06-20',
    title: '~ PPT 设计作品集',
    desc: '用代码做演示文稿，探索非模板化设计表达',
    category: 'project',
  },
];

/** 分类视觉配置 */
export const categoryConfig = {
  web:     { label: '网站开发', color: '#58a6ff', glow: 'rgba(88,166,255,0.2)' },
  project: { label: '课程项目', color: '#3fb950', glow: 'rgba(63,185,80,0.2)' },
  academic:{ label: '学业',     color: '#d29922', glow: 'rgba(210,153,34,0.2)' },
  life:    { label: '生活',     color: '#bc8cff', glow: 'rgba(188,140,255,0.2)' },
};
