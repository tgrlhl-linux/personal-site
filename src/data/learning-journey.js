/**
 * 学习成长旅程数据
 *
 * 从初中到大学的学习足迹，用折线图回溯成长轨迹。
 * Y 轴「成长指数」是综合知识广度、技能深度和项目经验的复合指标，
 * 反映认知能力的阶段性跃迁。
 *
 * @typedef {{ year: number, label: string, value: number, phase: string, events?: string[] }} JourneyPoint
 */

/** @type {JourneyPoint[]} */
export const journeyData = [
  // ═══════════ 初中：知识奠基 ═══════════
  { year: 2018, label: '初一', value: 5,  phase: 'middle-school',
    events: ['进入初中', '系统学习数学/英语/科学'] },
  { year: 2019, label: '初二', value: 12, phase: 'middle-school',
    events: ['逻辑思维初步建立', '信息科技基础'] },
  { year: 2020, label: '初三', value: 20, phase: 'middle-school',
    events: ['中考冲刺', '数理化基础成型'] },

  // ═══════════ 高中：能力跃升 ═══════════
  { year: 2021, label: '高一', value: 30, phase: 'high-school',
    events: ['进入高中', '理科分科', '学科深度提升'] },
  { year: 2022, label: '高二', value: 42, phase: 'high-school',
    events: ['编程启蒙', '自主学习方法形成'] },
  { year: 2023, label: '高三', value: 52, phase: 'high-school',
    events: ['高考备考', '知识体系一次整合'] },

  // ═══════════ 大学：专业深耕 ═══════════
  { year: 2024.25, label: '大一下', value: 62, phase: 'university',
    events: ['软件工程专业', 'C语言', '高等数学'] },
  { year: 2024.75, label: '大二上', value: 72, phase: 'university',
    events: ['Java/数据结构', '面向对象思维', 'Linux基础'] },
  { year: 2025.25, label: '大二下', value: 82, phase: 'university',
    events: ['数据库原理', '操作系统理论', 'Web开发入门'] },
  { year: 2025.75, label: '大三上', value: 92, phase: 'university',
    events: ['MiniSQL', 'Flask', 'Rust+egui', 'Hadoop', 'Shell'] },
  { year: 2026.50, label: '大三下', value: 100, phase: 'university',
    events: ['个人网站', '在线Demo', '全栈实践', '笔记体系化'] },
];

/** 阶段配色 */
export const phaseConfig = {
  'middle-school': { label: '初中', color: '#58a6ff', area: 'rgba(88,166,255,0.06)' },
  'high-school':   { label: '高中', color: '#d29922', area: 'rgba(210,153,34,0.06)' },
  'university':    { label: '大学', color: '#3fb950', area: 'rgba(63,185,80,0.06)' },
};
