# 磁盘调度算法模拟实验

## 项目概述

四种经典磁盘调度算法的 Python 模拟实现：FCFS、SSTF、LOOK（电梯调度）、CLOOK（单向扫描）。支持随机请求生成、详细的寻道过程输出、算法性能对比，以及基于 matplotlib 的静态可视化和动态动画演示。

## 架构设计

核心类 DiskScheduler 包含两个层级的实现：基础版（返回磁道号序列）和进程版（返回含进程名的详细序列）。每种算法都实现了对应的 with_processes 版本，用于输出格式化表格。

run_all() 方法统一编排所有算法的执行流程：生成请求序列 -> 逐算法计算并打印详细步骤表 -> 输出对比汇总 -> 按用户选择展示可视化。这种统一入口的设计使得新增算法只需在 algorithms 列表中添加一项。

可视化提供两种模式：静态模式以 2x2 子图对比四种算法的磁头移动轨迹；动态模式使用 matplotlib.animation.FuncAnimation 逐帧演示磁头移动，红色圆点标记当前位置，绿色圆点标记已访问柱面。

## 技术亮点

四算法统一接口：每种算法的返回格式统一为 (sequence, total_movement, avg_movement)，方便对比和排序输出。排序后的对比表自动展示性能优劣，SSTF 和 LOOK 通常表现最佳。

SSTF 的防饥饿设计：虽然基础 SSTF 可能导致饥饿，但实验通过限制请求序列长度（默认 10）来规避这一问题，教学场景中重点关注的是各算法的平均寻道长度差异。

CLOOK 相对 LOOK 的改进：CLOOK 单向扫描避免了 LOOK 在两端来回移动时的额外开销，具体表现为大跨度跳转只发生一次而非两次，在处理均匀分布的请求时响应时间更稳定。

## 设计决策

ProcessRequest 类用于封装进程名和磁道号，使得调度过程可以追踪每个请求的来源。这种设计虽然在简单模拟中略显冗余，但为后续扩展（如优先级、 deadline 等属性）保留了空间。

可视化模块独立可选，用户可在运行时选择是否展示，避免了无 GUI 环境下的运行失败。

## 关键代码解读

```python
def sstf(self):
    pending = self.requests.copy()
    current = self.start_cylinder
    while pending:
        distances = [(abs(req - current), req) for req in pending]
        distances.sort()
        min_distance, next_cyl = distances[0]
        total_movement += min_distance
        current = next_cyl
        pending.remove(next_cyl)
```

SSTF 的核心是每次从待处理列表中选距离最近的请求。计算所有距离 -> 排序 -> 取最小，这一 O(n^2) 的实现在请求数较少时直观且正确。LOOK 和 CLOOK 通过一次排序后将请求分为高低两部分，分别按方向顺序处理，时间复杂度降为 O(n log n)。
