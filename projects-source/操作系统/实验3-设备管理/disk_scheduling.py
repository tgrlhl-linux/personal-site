import random
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# 配置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ProcessRequest:
    """
    进程请求类，用于表示一个等待访问磁盘的进程请求
    
    属性:
        process_name: 进程名称，格式为 P1, P2, P3...
        cylinder: 进程要求访问的磁道号
    """
    def __init__(self, process_name, cylinder):
        self.process_name = process_name
        self.cylinder = cylinder
    
    def __repr__(self):
        return f"ProcessRequest({self.process_name}, {self.cylinder})"


class DiskScheduler:
    """
    磁盘调度器类，实现四种经典的磁盘调度算法
    
    属性:
        cylinders: 磁盘柱面总数，默认为200
        start_cylinder: 初始磁头位置，默认为100
        requests: 存储所有请求的磁道号列表
        request_table: 存储所有请求的ProcessRequest对象列表
    """
    
    def __init__(self, cylinders=200, start_cylinder=100):
        """
        初始化磁盘调度器
        
        参数:
            cylinders: 磁盘柱面总数
            start_cylinder: 初始磁头位置
        """
        self.cylinders = cylinders
        self.start_cylinder = start_cylinder
        self.requests = []          # 存储磁道号列表
        self.request_table = []     # 存储进程请求对象列表
    
    def generate_requests(self, length=10, min_cylinder=0, max_cylinder=None):
        """
        生成随机的进程请求I/O表
        
        参数:
            length: 请求序列长度，默认10
            min_cylinder: 最小磁道号，默认0
            max_cylinder: 最大磁道号，默认None（使用磁盘柱面总数-1）
        
        返回:
            request_table: 进程请求列表，每个元素是ProcessRequest对象
        """
        if max_cylinder is None:
            max_cylinder = self.cylinders - 1
        
        self.request_table = []
        for i in range(length):
            process_name = f"P{i+1}"
            cylinder = random.randint(min_cylinder, max_cylinder)
            self.request_table.append(ProcessRequest(process_name, cylinder))
        
        # 提取所有请求的磁道号到列表中
        self.requests = [req.cylinder for req in self.request_table]
        return self.request_table
    
    def print_request_table(self):
        """打印格式化的进程请求I/O表"""
        print("进程请求 I/O 表")
        print("=" * 40)
        print(f"| {'进程名':^8} | {'要求访问的磁道号':^12} |")
        print("-" * 40)
        for req in self.request_table:
            print(f"| {req.process_name:^8} | {req.cylinder:^12} |")
        print("=" * 40)
    
    def fcfs(self):
        """
        FCFS (先来先服务) 算法
        
        按照进程请求的先后顺序进行调度，不考虑磁道位置
        
        返回:
            sequence: 访问序列（磁道号列表）
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        # 访问序列从初始位置开始，然后按请求顺序访问
        sequence = [self.start_cylinder] + self.requests
        total_movement = 0
        
        # 计算总寻道长度
        for i in range(1, len(sequence)):
            total_movement += abs(sequence[i] - sequence[i-1])
        
        avg_movement = total_movement / len(self.requests)
        return sequence, total_movement, avg_movement
    
    def fcfs_with_processes(self):
        """
        FCFS算法的详细版本，返回包含进程名的访问序列
        
        返回:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        sequence = [(None, self.start_cylinder)]  # None表示初始位置，无进程
        total_movement = 0
        
        for req in self.request_table:
            sequence.append((req.process_name, req.cylinder))
            total_movement += abs(req.cylinder - sequence[-2][1])
        
        avg_movement = total_movement / len(self.request_table)
        return sequence, total_movement, avg_movement

    def sstf(self):
        """
        SSTF (最短寻道时间优先) 算法
        
        优先选择距离当前磁头最近的请求，使每次寻道时间最短
        
        返回:
            sequence: 访问序列（磁道号列表）
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        pending = self.requests.copy()  # 待处理的请求列表
        current = self.start_cylinder   # 当前磁头位置
        sequence = [current]            # 访问序列
        total_movement = 0

        # 循环处理所有待处理请求
        while pending:
            # 计算每个待处理请求与当前位置的距离
            distances = [(abs(req - current), req) for req in pending]
            distances.sort()  # 按距离排序
            
            # 选择距离最近的请求
            min_distance, next_cyl = distances[0]
            total_movement += min_distance
            current = next_cyl
            sequence.append(current)
            pending.remove(next_cyl)

        avg_movement = total_movement / len(self.requests)
        return sequence, total_movement, avg_movement
    
    def sstf_with_processes(self):
        """
        SSTF算法的详细版本，返回包含进程名的访问序列
        
        返回:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        pending = self.request_table.copy()
        current = self.start_cylinder
        sequence = [(None, self.start_cylinder)]
        total_movement = 0

        while pending:
            distances = [(abs(req.cylinder - current), req) for req in pending]
            distances.sort()
            min_distance, next_req = distances[0]
            total_movement += min_distance
            current = next_req.cylinder
            sequence.append((next_req.process_name, next_req.cylinder))
            pending.remove(next_req)

        avg_movement = total_movement / len(self.request_table)
        return sequence, total_movement, avg_movement

    def look(self):
        """
        LOOK (电梯调度) 算法
        
        磁头沿一个方向移动，处理完该方向所有请求后反向移动
        
        返回:
            sequence: 访问序列（磁道号列表）
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        if not self.requests:
            return [self.start_cylinder], 0, 0

        # 对请求进行排序
        sorted_requests = sorted(self.requests)
        current = self.start_cylinder
        sequence = [current]
        total_movement = 0

        # 分为大于等于当前位置和小于当前位置两部分
        higher = [req for req in sorted_requests if req >= current]
        lower = [req for req in sorted_requests if req < current]

        # 先处理当前方向（向外）的请求
        for req in higher:
            total_movement += abs(req - current)
            current = req
            sequence.append(current)

        # 方向改变后，处理反方向（向内）的请求
        for req in reversed(lower):
            total_movement += abs(req - current)
            current = req
            sequence.append(current)

        avg_movement = total_movement / len(self.requests)
        return sequence, total_movement, avg_movement
    
    def look_with_processes(self):
        """
        LOOK算法的详细版本，返回包含进程名的访问序列
        
        返回:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        if not self.request_table:
            return [(None, self.start_cylinder)], 0, 0

        sorted_reqs = sorted(self.request_table, key=lambda x: x.cylinder)
        current = self.start_cylinder
        sequence = [(None, self.start_cylinder)]
        total_movement = 0

        higher = [req for req in sorted_reqs if req.cylinder >= current]
        lower = [req for req in sorted_reqs if req.cylinder < current]

        for req in higher:
            total_movement += abs(req.cylinder - current)
            current = req.cylinder
            sequence.append((req.process_name, req.cylinder))

        for req in reversed(lower):
            total_movement += abs(req.cylinder - current)
            current = req.cylinder
            sequence.append((req.process_name, req.cylinder))

        avg_movement = total_movement / len(self.request_table)
        return sequence, total_movement, avg_movement

    def clook(self):
        """
        CLOOK (单向扫描) 算法
        
        对LOOK算法的改进，磁头只沿一个方向移动，到达最远端后直接回到另一端
        
        返回:
            sequence: 访问序列（磁道号列表）
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        if not self.requests:
            return [self.start_cylinder], 0, 0

        sorted_requests = sorted(self.requests)
        current = self.start_cylinder
        sequence = [current]
        total_movement = 0

        # 分为大于等于当前位置和小于当前位置两部分
        higher = [req for req in sorted_requests if req >= current]
        lower = [req for req in sorted_requests if req < current]

        # 先处理当前方向的请求
        for req in higher:
            total_movement += abs(req - current)
            current = req
            sequence.append(current)

        # 直接跳转到另一端，继续处理剩余请求
        for req in lower:
            total_movement += abs(req - current)
            current = req
            sequence.append(current)

        avg_movement = total_movement / len(self.requests)
        return sequence, total_movement, avg_movement
    
    def clook_with_processes(self):
        """
        CLOOK算法的详细版本，返回包含进程名的访问序列
        
        返回:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            total_movement: 总寻道长度
            avg_movement: 平均寻道长度
        """
        if not self.request_table:
            return [(None, self.start_cylinder)], 0, 0

        sorted_reqs = sorted(self.request_table, key=lambda x: x.cylinder)
        current = self.start_cylinder
        sequence = [(None, self.start_cylinder)]
        total_movement = 0

        higher = [req for req in sorted_reqs if req.cylinder >= current]
        lower = [req for req in sorted_reqs if req.cylinder < current]

        for req in higher:
            total_movement += abs(req.cylinder - current)
            current = req.cylinder
            sequence.append((req.process_name, req.cylinder))

        for req in lower:
            total_movement += abs(req.cylinder - current)
            current = req.cylinder
            sequence.append((req.process_name, req.cylinder))

        avg_movement = total_movement / len(self.request_table)
        return sequence, total_movement, avg_movement

    def animate_head_movement(self, sequence, algorithm_name):
        """
        动态演示磁头移动过程
        
        参数:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            algorithm_name: 算法名称，用于图表标题
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(-1, len(sequence))
        ax.set_ylim(-5, self.cylinders + 5)
        ax.set_xlabel('访问步骤')
        ax.set_ylabel('柱面号')
        ax.set_title(f'{algorithm_name} - 磁头移动动态演示')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(len(sequence)))
        
        # 初始化绘图元素
        line, = ax.plot([], [], 'b-', linewidth=2)       # 移动轨迹线
        head, = ax.plot([], [], 'ro', markersize=12, zorder=5)   # 当前磁头位置
        visited_points, = ax.plot([], [], 'go', markersize=8)    # 已访问点
        
        visited_x = []
        visited_y = []
        
        def init():
            """初始化动画"""
            line.set_data([], [])
            head.set_data([], [])
            visited_points.set_data([], [])
            return line, head, visited_points
        
        def update(frame):
            """动画更新函数"""
            if frame == 0:
                head.set_data([0], [sequence[0][1]])
                line.set_data([0], [sequence[0][1]])
                visited_x.append(0)
                visited_y.append(sequence[0][1])
                visited_points.set_data(visited_x, visited_y)
                return line, head, visited_points
            
            # 更新轨迹线
            x = list(range(frame + 1))
            y = [seq[1] for seq in sequence[:frame + 1]]
            line.set_data(x, y)
            head.set_data([frame], [sequence[frame][1]])
            
            # 更新已访问点
            visited_x.append(frame)
            visited_y.append(sequence[frame][1])
            visited_points.set_data(visited_x, visited_y)
            
            # 更新标题显示当前步骤
            if frame < len(sequence) - 1:
                ax.set_title(f'{algorithm_name} - 步骤 {frame}/{len(sequence)-2}')
            
            return line, head, visited_points
        
        # 创建动画
        anim = animation.FuncAnimation(fig, update, frames=len(sequence), 
                                      init_func=init, interval=800, blit=True, repeat=False)
        
        plt.tight_layout()
        plt.show()

    def visualize_static(self, sequence, algorithm_name, ax):
        """
        静态可视化磁头移动轨迹
        
        参数:
            sequence: 访问序列，每个元素是 (进程名, 磁道号) 元组
            algorithm_name: 算法名称，用于图表标题
            ax: matplotlib的Axes对象，用于绘制子图
        """
        ax.clear()
        steps = list(range(len(sequence)))
        cylinders = [seq[1] for seq in sequence]
        
        # 绘制轨迹线
        ax.plot(steps, cylinders, marker='o', linewidth=2, markersize=8, label='Head Movement')
        ax.set_xlabel('Access Order')
        ax.set_ylabel('Cylinder Number')
        ax.set_title(f'{algorithm_name}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 标注每个点的柱面号
        for i, (step, seq) in enumerate(zip(steps, sequence)):
            ax.annotate(f'{seq[1]}', (step, seq[1]), textcoords="offset points", 
                       xytext=(0,10), ha='center', fontsize=9)

    def run_all(self, request_length=10, show_static=False, show_animation=False):
        """
        运行所有四种算法并输出结果
        
        参数:
            request_length: 请求序列长度，默认10
            show_static: 是否显示静态可视化，默认False
            show_animation: 是否显示动态可视化，默认False
        
        返回:
            results: 包含四种算法结果的列表
        """
        # 生成请求序列
        self.generate_requests(request_length)
        
        # 打印磁盘参数
        print(f"磁盘参数:")
        print(f"  - 磁盘柱面总数: {self.cylinders}")
        print(f"  - 初始磁头位置: {self.start_cylinder}")
        print()
        
        # 打印进程请求I/O表
        self.print_request_table()
        print()

        # 定义四种算法
        algorithms = [
            ("FCFS (先来先服务)", self.fcfs_with_processes),
            ("SSTF (最短寻道时间优先)", self.sstf_with_processes),
            ("LOOK (电梯调度)", self.look_with_processes),
            ("CLOOK (单向扫描)", self.clook_with_processes)
        ]

        results = []
        # 运行每种算法并输出结果
        for name, func in algorithms:
            sequence, total, avg = func()
            results.append((name, sequence, total, avg))
            
            # 打印详细结果表
            print(f"{name}:")
            print("-" * 45)
            print(f"| {'步骤':^5} | {'进程名':^8} | {'访问磁道':^8} | {'移动距离':^8} |")
            print("-" * 45)
            
            cumulative = 0
            for i in range(1, len(sequence)):
                prev_cyl = sequence[i-1][1]
                curr_cyl = sequence[i][1]
                distance = abs(curr_cyl - prev_cyl)
                cumulative += distance
                process = sequence[i][0] if sequence[i][0] else "-"
                print(f"| {i:^5} | {process:^8} | {curr_cyl:^8} | {distance:^8} |")
            
            print("-" * 45)
            print(f"| {'总计':^5} | {'':^8} | {'':^8} | {cumulative:^8} |")
            print("-" * 45)
            print(f"  平均寻道长度: {avg:.2f}")
            print()

        # 打印算法对比总结
        print("=" * 55)
        print(f"| {'算法名称':<20} | {'总寻道长度':^12} | {'平均寻道长度':^12} |")
        print("-" * 55)
        # 按平均寻道长度排序输出
        for name, _, total, avg in sorted(results, key=lambda x: x[3]):
            print(f"| {name:<20} | {total:^12} | {avg:^12.2f} |")
        print("=" * 55)

        # 动态可视化
        if show_animation:
            print("\n正在准备动态可视化...")
            time.sleep(1)
            for name, sequence, _, _ in results:
                print(f"\n正在演示: {name}")
                self.animate_head_movement(sequence, name)
                choice = input("按 Enter 继续下一个，输入 'q' 跳过剩余动画: ").strip().lower()
                plt.close('all')
                if choice == 'q':
                    break

        # 静态可视化
        if show_static:
            print("\n正在生成静态可视化图表...")
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()

            for i, (name, sequence, _, _) in enumerate(results):
                self.visualize_static(sequence, name, axes[i])

            plt.suptitle('Disk Scheduling Algorithms Comparison', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.show()

        return results


if __name__ == "__main__":
    """主程序入口"""
    # 创建磁盘调度器实例
    scheduler = DiskScheduler(cylinders=200, start_cylinder=100)
    
    # 打印程序标题
    print("=" * 55)
    print("磁盘调度算法模拟程序")
    print("贵州大学计算机科学与技术学院")
    print("=" * 55)
    print()
    
    # 获取用户输入的请求序列长度
    while True:
        try:
            length = int(input("请输入请求序列长度 (默认10): ") or "10")
            if length > 0:
                break
            print("请输入正整数！")
        except ValueError:
            print("请输入有效的数字！")
    
    # 显示可视化选项
    print("\n可视化选项:")
    print("1. 不显示可视化")
    print("2. 仅静态可视化 (四种算法对比图)")
    print("3. 仅动态可视化 (逐个算法演示)")
    print("4. 复合可视化 (先动态演示，再显示静态对比图)")
    
    # 获取用户选择的可视化方式
    while True:
        choice = input("\n请选择可视化方式 (1/2/3/4): ")
        if choice in ['1', '2', '3', '4']:
            break
        print("请输入有效的选项 (1/2/3/4)！")
    
    # 根据选择设置可视化标志
    show_static = choice in ['2', '4']
    show_animation = choice in ['3', '4']
    
    # 打印分隔线
    print("\n" + "=" * 55)
    print("运行结果:")
    print("=" * 55)
    print()
    
    # 运行所有算法
    results = scheduler.run_all(length, show_static, show_animation)
    
    # 程序结束
    print("\n程序运行完毕！")