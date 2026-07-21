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
    events: ['进入遵义市第十二中学总校', '初考班级第四，开始发力'],
  },
  {
    year: 2018.75, label: '初一下', value: 20, phase: 'middle-school',
    events: ['巅峰期：班级第一，年级15/2000人', '期末 776.5/850，语文131.5年级第一'],
  },
  {
    year: 2019.50, label: '初二', value: 30, phase: 'middle-school',
    events: ['成绩稳在年级前列'],
  },
  {
    year: 2020.50, label: '初三', value: 38, phase: 'middle-school',
    events: ['状态下滑，中考 681/750', '保送省重点高中尖子班'],
  },

  // ═══════════ 高中：南白中学→观一高 ═══════════
  {
    year: 2021.25, label: '高一', value: 45, phase: 'high-school',
    events: ['遵义市南白中学·麒麟班（省重点）', '开始摆烂，成绩大幅下滑'],
  },
  {
    year: 2022.25, label: '高二', value: 48, phase: 'high-school',
    events: ['转学贵阳市观山湖区第一高级中学', '持续摆烂'],
  },
  {
    year: 2023.25, label: '高三', value: 52, phase: 'high-school',
    events: ['临时抱佛脚，无力回天', '高考 576 分，进入贵州大学'],
  },

  // ═══════════ 大学：贵州大学 软件工程 ═══════════
  {
    year: 2024.25, label: '大一下', value: 58, phase: 'university',
    events: ['软工专业入门', 'C语言、高数', '绩点不到3.43，玩太爽'],
  },
  {
    year: 2024.75, label: '大二上', value: 68, phase: 'university',
    events: ['Java/数据结构', '开始发力，拉升绩点'],
  },
  {
    year: 2025.25, label: '大二下', value: 80, phase: 'university',
    events: ['数据库原理/操作系统', 'Linux/大数据', '院团委组织部部长'],
  },
  {
    year: 2025.75, label: '大三上', value: 92, phase: 'university',
    events: ['MiniSQL/Rust/Flask/Hadoop', '三下乡（清华合办）', '酒博会优秀志愿者'],
  },
  {
    year: 2026.50, label: '大三下', value: 100, phase: 'university',
    events: ['个人网站/全栈实践', '贵州教育报发表文章', '预备党员', '笔记体系化'],
  },
];

/** 阶段配色 */
export const phaseConfig = {
  'middle-school': { label: '初中·遵义十二中', color: '#58a6ff', area: 'rgba(88,166,255,0.06)' },
  'high-school':   { label: '高中·南白→观一高', color: '#d29922', area: 'rgba(210,153,34,0.06)' },
  'university':    { label: '大学·贵州大学', color: '#3fb950', area: 'rgba(63,185,80,0.06)' },
};
