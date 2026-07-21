/**
 * 学习成长旅程数据
 *
 * 从初中到大学的学习足迹，用折线图回溯成长轨迹。
 * Y 轴「成长指数」是综合知识广度、技能深度和学业表现的复合指标。
 *
 * @typedef {{ year: number, label: string, value: number, phase: string, events?: string[] }} JourneyPoint
 */

/** @type {JourneyPoint[]} */
export const journeyData = [
  // ═══════════ 初中：遵义市第十二中学总校 ═══════════
  {
    year: 2018.25, label: '初一上', value: 8, phase: 'middle-school',
    events: ['进入遵义市第十二中学总校'],
  },
  {
    year: 2018.75, label: '初一下', value: 20, phase: 'middle-school',
    events: ['成绩进入前列，奠定学业基础'],
  },
  {
    year: 2019.50, label: '初二', value: 30, phase: 'middle-school',
    events: ['保持良好学习状态'],
  },
  {
    year: 2020.50, label: '初三', value: 38, phase: 'middle-school',
    events: ['保送省重点高中尖子班'],
  },

  // ═══════════ 高中：南白中学→观一高 ═══════════
  {
    year: 2021.25, label: '高一', value: 45, phase: 'high-school',
    events: ['遵义市南白中学·麒麟班（省重点）'],
  },
  {
    year: 2022.25, label: '高二', value: 48, phase: 'high-school',
    events: ['转学贵阳市观山湖区第一高级中学'],
  },
  {
    year: 2023.25, label: '高三', value: 52, phase: 'high-school',
    events: ['高考进入贵州大学'],
  },

  // ═══════════ 大学：贵州大学 软件工程（2024-2028）═══════════
  {
    year: 2024.75, label: '大一上', value: 58, phase: 'university',
    events: ['软件工程专业入门'],
  },
  {
    year: 2025.25, label: '大一下', value: 68, phase: 'university',
    events: ['开始发力专业课程'],
  },
  {
    year: 2025.75, label: '大二上', value: 80, phase: 'university',
    events: ['数据库原理/操作系统/Linux/大数据', '院团委组织部副部长'],
  },
  {
    year: 2026.25, label: '大二下', value: 92, phase: 'university',
    events: ['MiniSQL/Rust/Flask/Hadoop 全栈实践', '三下乡（清华合办）', '酒博会优秀志愿者'],
  },
  {
    year: 2026.75, label: '大三上', value: 100, phase: 'university',
    events: ['个人网站全栈搭建', '贵州教育报发表文章', '预备党员'],
  },
];

/** 阶段配色 */
export const phaseConfig = {
  'middle-school': { label: '初中·遵义十二中', color: '#58a6ff', area: 'rgba(88,166,255,0.06)' },
  'high-school':   { label: '高中·南白→观一高', color: '#d29922', area: 'rgba(210,153,34,0.06)' },
  'university':    { label: '大学·贵州大学', color: '#3fb950', area: 'rgba(63,185,80,0.06)' },
};
