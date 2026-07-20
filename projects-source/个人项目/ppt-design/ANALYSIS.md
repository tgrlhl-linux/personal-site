# PPT 设计作品集

## 项目概述

用 HTML/CSS/JavaScript 呈现的 PPT 设计作品集。无需 PPT 软件，浏览器打开即用。每套作品独立视觉主题，覆盖日系动漫、古风聊斋、现代演讲三种风格，另有 AI 认知主题在内。

## 作品清单

| 作品 | 文件 | 风格 | 特点 |
|------|------|------|------|
| 动漫文化导览 | `anime.html` | 日系暗色 | 渐变光效、信息分层、产业数据可视化 |
| 聊斋志异 | `ghost-stories.html` | 古风暗色 | 书法字体、墨迹纹理、竖排文字、朱砂点缀 |
| 演讲艺术 | `presentation-mastery.html` | 现代暖色 | 极简版式、信息密度高、实战框架 |
| AI 认知跃迁 | `index.html` | 科技暗色 | 无衬线字体、1920×1080 固定舞台、打印支持 |

## 技术架构

### 幻灯片引擎（通用框架）

所有作品共享相同的翻页系统：

```
CSS:    .slide.active → visibility + opacity 过渡
JS:     keydown 监听（ArrowLeft/Right） + 导航点点击
布局:   固定 1920×1080 舞台（部分作品使用视口自适应）
```

### 核心代码量

```javascript
// 通用翻页引擎（每套约 30 行）
let current = 0;
const slides = document.querySelectorAll('.slide');

function goTo(index) {
  slides.forEach(s => s.classList.remove('active'));
  slides[index].classList.add('active');
  current = index;
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') goTo(current + 1);
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') goTo(current - 1);
});
```

### 设计系统（以聊斋为例）

| 设计元素 | 实现 | 效果 |
|---------|------|------|
| 背景 | `radial-gradient` 多层叠加 | 墨迹晕染感 |
| 标题 | `writing-mode: vertical-rl` | 竖排古风 |
| 主色 | `#c0392b` 朱砂红 | 古典点缀 |
| 字体 | `Noto Serif SC` | 书法质感 |
| 纹理 | `::before` 伪元素渐变 | 纸张肌理 |

## 设计原则

1. **风格统一**：每套作品内部保持色彩、字体、间距的系统一致性
2. **内容优先**：版式为信息传达服务，不做过度装饰
3. **高密度**：单页承载 5-8 个信息点，无废页
4. **可访问性**：纯键盘操作，色觉友好
