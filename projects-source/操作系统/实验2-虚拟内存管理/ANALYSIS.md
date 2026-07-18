# 虚拟内存管理模拟实验

## 项目概述

Python 实现的虚拟内存管理系统模拟器，核心功能为页面置换算法的对比实验。实现了 LRU（最近最久未使用）和二次机会（Second Chance）两种置换策略，支持多进程并发模拟、比例分配策略、缺页中断处理，并配备 Pygame 可视化展示。

## 架构设计

系统围绕 Process 类构建，每个进程维护独立的页表、帧映射和置换算法数据结构。主流程分为三个实验阶段：初始页表生成与输出、无缺页访问测试、缺页测试与算法对比。每个阶段都输出详细的物理地址映射和页表状态。

分配策略采用 proportional_alloc() 按进程页数比例分配物理帧，并通过多次补充分配确保无帧浪费。测试数据支持从 test_data.txt 读取和自动生成两种方式，自动生成的序列设计为三个阶段（访问初始页、强制置换、混合访问）以凸显算法差异。

## 技术亮点

Pygame 实时可视化：draw_simulation() 函数以赛博朋克风格渲染每个进程的帧分配情况和当前访问状态。采用发光字体、帧高亮、引用位 R 值显示和时钟指针箭头等视觉元素，将 LRU 和二次机会算法的行为差异直观呈现。

LRU 的高效实现：使用 Python 的 OrderedDict 维护帧的访问顺序，每次命中时调用 move_to_end() 将帧移到最后，淘汰时 popitem(last=False) 取最久未使用的帧。避免了每次访问排序的 O(n) 开销。

完整的实验验证流程：包含前提校验（帧数 < 页数才能产生缺页）、无缺页测试（验证命中时的行为）、缺页测试（对比两种算法表现），并输出详细的结论分析和适用场景说明。

## 设计决策

固定随机种子 seed(42) 保证实验结果可复现，这是教学实验的关键要求。Pygame 动画帧率设为 2 FPS，确保观察者能看清每次缺页操作的完整过程。测试序列设计为 50 个地址左右，平衡了实验的全面性和演示的流畅度。

## 关键代码解读

```python
def access_lru(self, addr):
    if page in self.page_table:
        self.lru_order.move_to_end(frame)
        return frame, False, None, phys_addr
    self.lru_faults += 1
    victim_frame, victim_page = self.lru_order.popitem(last=False)
    # 换入新页...
```

LRU 的核心逻辑仅 3 行关键代码：命中时 move_to_end 更新访问顺序，缺页时 popitem(last=False) 淘汰最久未使用帧。这种基于 OrderedDict 的双向链表 + 哈希表实现，与理论教材中描述的 LRU 栈实现完全对应。
