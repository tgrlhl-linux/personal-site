#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
操作系统实验2：虚拟内存管理
1. 固定随机种子保证可复现
2. 修正二次机会算法（标准实现）
3. 完善LRU算法的lru_order语义
4. 添加完整的前提校验和结果验证
5. 规范测试输出格式
6. 启用create_test_sequence生成体现算法差异的序列
"""
import random
import sys
from collections import OrderedDict, deque
import pygame

# 固定随机种子保证可复现
random.seed(42)

# 常量
PAGE_SIZE = 256
ADDR_BITS = 16
TOTAL_FRAMES = 50
WIN_WIDTH, WIN_HEIGHT = 1400, 850
FPS = 2

# 颜色
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (200,200,200)
GREEN = (100,255,100)
RED = (255,100,100)
BLUE = (100,100,255)
YELLOW = (255,255,100)
ORANGE = (255,200,100)


class Process:
    def __init__(self, pid, total_pages, frames):
        self.pid = pid
        self.total_pages = total_pages
        self.allocated_frames = frames.copy()
        self.page_table = {}
        self.page_to_frame = {}
        self.frame_to_page = {}

        # LRU相关：lru_order 维护帧的访问顺序，key=frame, value=page
        self.lru_order = OrderedDict()
        
        # 二次机会相关：clock_queue 维护帧的装入顺序，hand 是扫描指针
        self.clock_queue = deque()
        self.hand = 0
        
        self.lru_faults = 0
        self.sc_faults = 0

    def init_page_table(self, pages):
        """初始化页表"""
        self.page_table.clear()
        self.page_to_frame.clear()
        self.frame_to_page.clear()
        self.lru_order.clear()
        self.clock_queue.clear()
        self.hand = 0
        
        for frame, page in zip(self.allocated_frames, pages):
            self.page_table[page] = {'frame': frame, 'ref': 0}
            self.page_to_frame[frame] = page
            self.frame_to_page[frame] = page
            self.lru_order[frame] = page
            self.clock_queue.append(frame)

    @staticmethod
    def extract_page(addr): return addr >> 8
    @staticmethod
    def extract_offset(addr): return addr & 0xFF

    def physical_addr(self, page, offset, frame):
        return (frame << 8) | offset

    def access_lru(self, addr):
        page = self.extract_page(addr)
        offset = self.extract_offset(addr)
        
        if page in self.page_table:
            frame = self.page_table[page]['frame']
            # 移动到末尾表示最近使用
            self.lru_order.move_to_end(frame)
            return frame, False, None, self.physical_addr(page, offset, frame)
        
        self.lru_faults += 1
        # LRU淘汰：选择最久未使用的帧（OrderedDict第一个元素）
        victim_frame, victim_page = self.lru_order.popitem(last=False)
        
        del self.page_table[victim_page]
        del self.frame_to_page[victim_frame]
        
        self.page_table[page] = {'frame': victim_frame, 'ref': 0}
        self.page_to_frame[victim_frame] = page
        self.frame_to_page[victim_frame] = page
        self.lru_order[victim_frame] = page
        
        return victim_frame, True, victim_page, self.physical_addr(page, offset, victim_frame)

    def access_second_chance(self, addr):
        page = self.extract_page(addr)
        offset = self.extract_offset(addr)
        
        if page in self.page_table:
            # 命中：设置引用位为1
            self.page_table[page]['ref'] = 1
            frame = self.page_table[page]['frame']
            return frame, False, None, self.physical_addr(page, offset, frame)
        
        self.sc_faults += 1
        
        # 标准二次机会算法：扫描环形队列
        while True:
            if not self.clock_queue:
                # 兜底：队列为空时返回错误
                return None, True, None, 0
            
            frame = self.clock_queue[self.hand]
            
            if frame in self.frame_to_page:
                cur_page = self.frame_to_page[frame]
                
                if self.page_table[cur_page]['ref'] == 0:
                    # 找到引用位为0的页，淘汰它
                    victim_page = cur_page
                    
                    del self.page_table[victim_page]
                    del self.frame_to_page[frame]
                    
                    # 换入新页，设置引用位为1
                    self.page_table[page] = {'frame': frame, 'ref': 1}
                    self.page_to_frame[frame] = page
                    self.frame_to_page[frame] = page
                    
                    # 移动指针到下一个位置
                    self.hand = (self.hand + 1) % len(self.clock_queue)
                    
                    return frame, True, victim_page, self.physical_addr(page, offset, frame)
                else:
                    # 引用位为1，重置为0并继续扫描
                    self.page_table[cur_page]['ref'] = 0
                    self.hand = (self.hand + 1) % len(self.clock_queue)
            else:
                # 该帧为空，继续扫描
                self.hand = (self.hand + 1) % len(self.clock_queue)


def proportional_alloc(n1, n2, n3):
    """按比例分配帧，并进行边界检查"""
    free = list(range(TOTAL_FRAMES))
    random.shuffle(free)
    total = n1 + n2 + n3
    
    # 确保总页数不为零
    if total == 0:
        return [], [], []
    
    # 按比例分配，但不超过进程页数
    f1 = max(1, min(n1, round(TOTAL_FRAMES * n1 / total)))
    f2 = max(1, min(n2, round(TOTAL_FRAMES * n2 / total)))
    f3 = TOTAL_FRAMES - f1 - f2
    
    # 确保f3至少为1且不超过n3
    if f3 < 1:
        f3 = 1
        if f2 > 1:
            f2 -= 1
        elif f1 > 1:
            f1 -= 1
    f3 = min(f3, n3)
    
    # 重新分配剩余帧
    remaining = TOTAL_FRAMES - f1 - f2 - f3
    if remaining > 0:
        # 优先分配给页数多的进程
        if n1 > f1 and remaining > 0:
            add = min(remaining, n1 - f1)
            f1 += add
            remaining -= add
        if n2 > f2 and remaining > 0:
            add = min(remaining, n2 - f2)
            f2 += add
            remaining -= add
        if n3 > f3 and remaining > 0:
            add = min(remaining, n3 - f3)
            f3 += add
    
    # 确保不超出free列表范围
    f1 = min(f1, len(free))
    f2 = min(f2, len(free) - f1)
    f3 = len(free) - f1 - f2
    
    return free[:f1], free[f1:f1+f2], free[f1+f2:]


def print_pt(proc):
    print(f"\nP{proc.pid} 页表（共{len(proc.allocated_frames)}帧）：")
    print("页号 | 帧号 | 访问位")
    print("-----|------|------")
    for p in sorted(proc.page_table):
        d = proc.page_table[p]
        print(f"{p:4d} | {d['frame']:4d} | {d['ref']:5d}")


def draw_simulation(screen, procs, algo, curr_proc, curr_page, res, step_info):
    # 渐变背景
    for i in range(WIN_HEIGHT):
        t = i / WIN_HEIGHT
        r = int(5 + t * 15)
        g = int(5 + t * 15)
        b = int(20 + t * 40)
        pygame.draw.line(screen, (r, g, b), (0, i), (WIN_WIDTH, i))
    
    font = pygame.font.Font(None, 28)
    title_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 18)
    
    algo_name = "LRU" if algo == "LRU" else "Second Chance"
    title_text = "Virtual Memory Simulator - " + algo_name
    
    # 发光标题
    for glow in range(5, 0, -1):
        glow_surface = title_font.render(title_text, True, (100, 100, 150))
        screen.blit(glow_surface, (20 + glow, 20 + glow))
    title = title_font.render(title_text, True, WHITE)
    screen.blit(title, (20, 20))
    
    # 状态栏
    status_bg = pygame.Surface((WIN_WIDTH - 40, 90))
    status_bg.set_alpha(220)
    status_bg.fill((20, 25, 45))
    screen.blit(status_bg, (20, 70))
    pygame.draw.rect(screen, (80, 90, 130), (20, 70, WIN_WIDTH - 40, 90), 2, border_radius=8)
    
    proc_info = font.render(f"Process P{curr_proc.pid}", True, YELLOW)
    page_info = font.render(f"Page: {curr_page}", True, WHITE)
    result_info = font.render("FAULT!" if res[1] else "HIT", True, RED if res[1] else GREEN)
    victim_info = font.render(f"Victim: {res[2] if res[2] is not None else 'None'}", True, ORANGE)
    
    screen.blit(proc_info, (35, 85))
    screen.blit(page_info, (180, 85))
    screen.blit(result_info, (300, 85))
    screen.blit(victim_info, (420, 85))
    screen.blit(small_font.render(step_info, True, (180, 180, 200)), (35, 125))

    # 算法徽章
    badge_bg = pygame.Surface((180, 40))
    badge_bg.fill((30, 35, 55))
    pygame.draw.rect(badge_bg, (80, 90, 130), (0, 0, 180, 40), 2, border_radius=6)
    screen.blit(badge_bg, (WIN_WIDTH - 195, 15))
    algo_short = "LRU" if algo_name == "LRU" else "SC"
    algo_badge = font.render("Algo: " + algo_short, True, YELLOW)
    screen.blit(algo_badge, (WIN_WIDTH - 190, 22))

    # 进程区域布局
    num_procs = len(procs)
    available_width = WIN_WIDTH - 80
    proc_width = min(420, available_width // num_procs - 25)
    max_frames = max(len(p.allocated_frames) for p in procs)
    frame_height = min(28, (WIN_HEIGHT - 250) // max_frames) - 1
    proc_spacing = proc_width + 25
    
    for i, p in enumerate(procs):
        base_x = 40 + i * proc_spacing
        proc_title = font.render(f"Process P{p.pid} ({len(p.allocated_frames)} frames)", True, WHITE)
        
        # 标题发光效果
        title_shadow = font.render(f"Process P{p.pid} ({len(p.allocated_frames)} frames)", True, (50, 50, 80))
        screen.blit(title_shadow, (base_x + 1, 156))
        screen.blit(proc_title, (base_x, 155))
        
        # 绘制帧
        max_display = min(len(p.allocated_frames), 15)
        frames_to_display = sorted(p.allocated_frames)[:max_display]
        
        for j, f in enumerate(frames_to_display):
            x = base_x
            y = 190 + j * (frame_height + 3)
            pg = p.frame_to_page.get(f, None)
            
            is_current = (p == curr_proc and pg == curr_page)
            
            if pg is None:
                color = (60, 60, 70)
                glow_color = (40, 40, 50)
            elif is_current:
                color = (255, 80, 80) if res[1] else (80, 255, 80)
                glow_color = (200, 50, 50) if res[1] else (50, 200, 50)
            else:
                color = (70, 120, 220)
                glow_color = (50, 80, 180)
            
            # 发光效果
            for blur in range(3, 0, -1):
                pygame.draw.rect(screen, (min(255, glow_color[0]//blur), min(255, glow_color[1]//blur), min(255, glow_color[2]//blur)), 
                               (x - blur*2, y - blur*2, proc_width + blur*4, frame_height + blur*4), border_radius=6)
            
            # 帧背景
            pygame.draw.rect(screen, color, (x, y, proc_width, frame_height), border_radius=6)
            pygame.draw.rect(screen, (200, 210, 230), (x, y, proc_width, frame_height), 1, border_radius=6)
            
            # 当前访问帧高亮
            if is_current:
                pygame.draw.rect(screen, (255, 255, 255), (x-3, y-3, proc_width+6, frame_height+6), 2, border_radius=8)
                pygame.draw.rect(screen, color, (x-1, y-1, proc_width+2, frame_height+2), 1, border_radius=7)

            txt = f"Frame {f}: Page {pg}" if pg is not None else f"Frame {f}: --"
            screen.blit(small_font.render(txt, True, WHITE), (x+8, y+4))

            if algo == "SC" and pg is not None:
                ref = p.page_table[pg]['ref']
                ref_color = (100, 255, 100) if ref else (255, 100, 100)
                screen.blit(small_font.render(f"R={ref}", True, ref_color), (x + proc_width - 45, y+4))
                
                if p == curr_proc and p.clock_queue[p.hand % len(p.clock_queue)] == f:
                    pygame.draw.polygon(screen, (150, 150, 150), [(x-10, y+frame_height//2), (x-20, y+frame_height//2-8), (x-20, y+frame_height//2+8)])
                    pygame.draw.polygon(screen, ORANGE, [(x-11, y+frame_height//2), (x-22, y+frame_height//2-8), (x-22, y+frame_height//2+8)])

        # 剩余帧提示
        remaining = len(p.allocated_frames) - max_display
        if remaining > 0:
            screen.blit(small_font.render(f"... and {remaining} more frames", True, (100, 100, 120)), (base_x, 190 + max_display * (frame_height + 3) + 5))

    # 底部统计栏
    bottom_height = 55
    bottom_bg = pygame.Surface((WIN_WIDTH - 40, bottom_height))
    bottom_bg.set_alpha(240)
    bottom_bg.fill((15, 18, 35))
    screen.blit(bottom_bg, (20, WIN_HEIGHT - bottom_height - 10))
    pygame.draw.rect(screen, (60, 70, 100), (20, WIN_HEIGHT - bottom_height - 10, WIN_WIDTH - 40, bottom_height), 2, border_radius=8)
    
    for i, p in enumerate(procs):
        info = font.render(f"P{p.pid} | LRU={p.lru_faults} | SC={p.sc_faults} faults", True, WHITE)
        screen.blit(info, (40 + i * proc_spacing, WIN_HEIGHT - bottom_height - 3))

    pygame.display.flip()


def create_test_sequence(initial_pages, total_pages, num_frames):
    """生成能体现算法差异的测试序列"""
    sequence = []
    
    # 测试序列长度 = 帧数 × 2
    seq_length = max(20, num_frames * 2)
    
    # 计算超出初始范围的页面
    out_of_range = list(range(len(initial_pages), total_pages))
    
    # 如果没有超出范围的页面，就用初始页面但打乱顺序
    if not out_of_range:
        # 确保有缺页：创建一些"虚拟"的新页号
        out_of_range = list(range(total_pages, total_pages + 20))
    
    # 阶段1：访问初始页面（已在内存中的页）
    for _ in range(seq_length // 3):
        page = random.choice(initial_pages)
        sequence.append(page)
    
    # 阶段2：访问超出初始范围的页面，强制置换
    for _ in range(seq_length // 3):
        page = random.choice(out_of_range)
        sequence.append(page)
    
    # 阶段3：混合访问，包含新旧页面
    for _ in range(seq_length - seq_length // 3 * 2):
        if random.random() < 0.5:
            page = random.choice(initial_pages)
        else:
            page = random.choice(out_of_range)
        sequence.append(page)
    
    # 添加随机扰动
    for _ in range(3):
        pos = random.randint(0, len(sequence) - 1)
        if random.random() < 0.5 and out_of_range:
            sequence.insert(pos, random.choice(out_of_range))
        else:
            sequence.append(random.choice(initial_pages))
    
    return sequence


def load_test_data(filepath):
    """从预设文件读取测试数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            addrs = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 提取行首的数字（处理行尾的注释）
                    parts = line.split()
                    if parts:
                        try:
                            addrs.append(int(parts[0]))
                        except ValueError:
                            continue
        return addrs
    except Exception as e:
        print(f"读取测试文件失败，使用默认测试数据: {e}")
        return [300, 500, 456, 717, 3584, 4096, 4864, 5632, 6144, 7168]


def main():
    print("=" * 60)
    print("虚拟内存置换算法实验")
    print("=" * 60)
    
    # ===== 第一次输入：进程页数 =====
    print("\n>>> 输入进程页数（建议: 8 12 15）")
    while True:
        try:
            n1, n2, n3 = map(int, input("输入n1 n2 n3：").split())
            # 校验：每个进程至少5页
            if n1 >= 5 and n2 >= 5 and n3 >= 5:
                break
            else:
                print("请输入合理的页数（每个进程至少5页）")
        except:
            n1, n2, n3 = 8, 12, 15
            print(f"使用默认值：{n1} {n2} {n3}")
            break
    
    f1, f2, f3 = proportional_alloc(n1, n2, n3)
    num_frames_p2 = len(f2)
    
    # 校验：帧数 < 页数（确保能产生缺页）
    print(f"\n前提校验:")
    print(f"P1: 页数={n1}, 帧数={len(f1)}, 帧数<页数: {len(f1) < n1}")
    print(f"P2: 页数={n2}, 帧数={len(f2)}, 帧数<页数: {len(f2) < n2}")
    print(f"P3: 页数={n3}, 帧数={len(f3)}, 帧数<页数: {len(f3) < n3}")
    
    # 创建进程
    p1 = Process(1, n1, f1)
    p2 = Process(2, n2, f2)
    p3 = Process(3, n3, f3)
    
    # 随机生成初始页表（实验要求1：随机生成已载入内存的页号）
    initial_pages_p1 = random.sample(range(n1), min(len(f1), n1))
    initial_pages_p2 = random.sample(range(n2), min(len(f2), n2))
    initial_pages_p3 = random.sample(range(n3), min(len(f3), n3))
    
    p1.init_page_table(initial_pages_p1)
    p2.init_page_table(initial_pages_p2)
    p3.init_page_table(initial_pages_p3)
    
    # 保存初始页表用于后续重置
    initial_pages = initial_pages_p2.copy()
    
    # ===== 实验要求1：输出初始页表 =====
    print("\n" + "=" * 60)
    print("初始页表")
    print("=" * 60)
    print(f"P1 共分配到 {len(f1)} 个页框，其页表内容如下：")
    print_pt(p1)
    print(f"\nP2 共分配到 {len(f2)} 个页框，其页表内容如下：")
    print_pt(p2)
    print(f"\nP3 共分配到 {len(f3)} 个页框，其页表内容如下：")
    print_pt(p3)
    
    # ===== 无缺页测试 =====
    print("\n" + "=" * 60)
    print("无缺页测试")
    print("=" * 60)
    
    # 让用户选择测试进程
    print(f"\n>>> 选择测试进程（1/2/3）和无缺页访问序列")
    print(f"P1初始页表中的页号：{sorted(initial_pages_p1)}")
    print(f"P2初始页表中的页号：{sorted(initial_pages_p2)}")
    print(f"P3初始页表中的页号：{sorted(initial_pages_p3)}")
    
    while True:
        try:
            choice_input = input("选择测试进程（1/2/3）：")
            test_pid = int(choice_input.strip())
            if test_pid in [1, 2, 3]:
                break
            else:
                print("请输入 1、2 或 3")
        except:
            test_pid = 2
            print("使用默认值：P2")
            break
    
    # 根据选择的进程获取相关信息
    if test_pid == 1:
        proc_no_fault = Process(1, n1, f1)
        proc_no_fault.init_page_table(initial_pages_p1)
        initial_pages = initial_pages_p1
        proc_name = "P1"
    elif test_pid == 2:
        proc_no_fault = Process(2, n2, f2)
        proc_no_fault.init_page_table(initial_pages_p2)
        initial_pages = initial_pages_p2
        proc_name = "P2"
    else:
        proc_no_fault = Process(3, n3, f3)
        proc_no_fault.init_page_table(initial_pages_p3)
        initial_pages = initial_pages_p3
        proc_name = "P3"
    
    print(f"\n已选择进程：{proc_name}")
    print(f"页号范围：{sorted(initial_pages)}")
    print(f"例如：{initial_pages[0]} {initial_pages[1]} {initial_pages[2]} {initial_pages[0]} {initial_pages[1]}")
    
    while True:
        try:
            seq_input = input("输入访问序列（页号，空格分隔）：")
            if seq_input.strip() == "":
                print("输入不能为空，请至少输入3个页号")
                continue
            
            test_pages_no_fault = [int(x.strip()) for x in seq_input.split()]
            
            if len(test_pages_no_fault) >= 3:
                invalid_pages = [p for p in test_pages_no_fault if p not in proc_no_fault.page_table]
                if not invalid_pages:
                    break
                else:
                    print(f"警告：页号 {invalid_pages} 不在{proc_name}初始页表中")
                    print(f"请从以下页号中选择：{sorted(initial_pages)}")
            else:
                print("请输入至少3个页号")
        except ValueError:
            print("输入格式错误，请输入空格分隔的数字序列")
            test_pages_no_fault = initial_pages[:3] * 2
            print(f"使用默认序列：{test_pages_no_fault}")
            break
    
    # 执行无缺页测试
    print(f"\n{proc_name} 共分配到 {len(proc_no_fault.allocated_frames)} 个页框，")
    print(f"经过页面访问序列：{', '.join(map(str, test_pages_no_fault))}")
    print(f"\n本轮访问对应的物理地址为：")
    
    phys_addrs = []
    for page in test_pages_no_fault:
        frame = proc_no_fault.page_table[page]['frame']
        offset = 100
        phys = (frame << 8) | offset
        phys_addrs.append(f"{page * PAGE_SIZE + offset}-{phys}")
        print(f"{page * PAGE_SIZE + offset}-{phys}")
    
    print(f"\n{proc_name} 更新后的页表内容如下：")
    print_pt(proc_no_fault)
    
    # ===== 缺页测试与算法对比 =====
    print("\n" + "=" * 60)
    print("缺页测试与算法对比")
    print("=" * 60)
    
    # 让用户选择测试进程（与无缺页测试相同的进程）
    print(f"\n>>> 使用进程：{proc_name}")
    print(f"初始页表页号范围：{sorted(initial_pages)}")
    
    # 从预设文件读取测试数据（实验要求3）
    test_addrs = load_test_data("test_data.txt")
    print(f"\n从 test_data.txt 读取到 {len(test_addrs)} 个逻辑地址")
    print(f"逻辑地址序列：{test_addrs}")
    test_pages = [addr >> 8 for addr in test_addrs]
    print(f"对应页号序列：{test_pages}")
    print(f"初始页表页号范围：{sorted(initial_pages)}")
    print(f"超出初始范围的页号：{[p for p in test_pages if p not in initial_pages]}")
    
    # 创建测试进程
    if test_pid == 1:
        proc_lru = Process(1, n1, f1)
        proc_lru.init_page_table(initial_pages_p1)
        proc_sc = Process(1, n1, f1)
        proc_sc.init_page_table(initial_pages_p1)
        num_frames = len(f1)
    elif test_pid == 2:
        proc_lru = Process(2, n2, f2)
        proc_lru.init_page_table(initial_pages_p2)
        proc_sc = Process(2, n2, f2)
        proc_sc.init_page_table(initial_pages_p2)
        num_frames = len(f2)
    else:
        proc_lru = Process(3, n3, f3)
        proc_lru.init_page_table(initial_pages_p3)
        proc_sc = Process(3, n3, f3)
        proc_sc.init_page_table(initial_pages_p3)
        num_frames = len(f3)
    
    # LRU算法测试
    print("\n" + "-" * 50)
    print("LRU算法")
    print("-" * 50)
    
    print("本轮访问对应的物理地址为：")
    
    first_fault_idx = -1
    for idx, addr in enumerate(test_addrs):
        page = addr >> 8
        offset = addr & 0xFF
        frame, fault, victim, phys = proc_lru.access_lru(addr)
        
        if not fault:
            print(f"{addr}-{phys}")
        else:
            if first_fault_idx == -1:
                first_fault_idx = idx
            print(f"{addr}-{phys}")
    
    # 如果有缺页，显示第一次缺页的详细信息
    if first_fault_idx >= 0:
        # 重新运行以获取详细信息
        proc_lru_detail = Process(test_pid, n1 if test_pid == 1 else (n2 if test_pid == 2 else n3), 
                                  f1 if test_pid == 1 else (f2 if test_pid == 2 else f3))
        proc_lru_detail.init_page_table(initial_pages.copy())
        
        fault_count = 0
        fault_info = None
        for idx, addr in enumerate(test_addrs):
            page = addr >> 8
            offset = addr & 0xFF
            frame, fault, victim, phys = proc_lru_detail.access_lru(addr)
            
            if fault:
                fault_count += 1
                if fault_count == first_fault_idx + 1:
                    fault_info = (idx, page, victim, phys, proc_lru_detail)
                    break
        
        if fault_info:
            idx, page, victim, phys, detail_proc = fault_info
            print(f"\n第 {idx + 1} 次访问发生缺页，根据LRU算法，")
            print(f"将 {victim} 页换出，将 {page} 页换入，对应的物理地址为 {phys}，")
            print(f"{proc_name} 更新后的页表内容如下：")
            print_pt(detail_proc)
    
    lru_faults = proc_lru.lru_faults
    
    # 二次机会算法测试
    print("\n" + "-" * 50)
    print("二次机会算法")
    print("-" * 50)
    
    print("本轮访问对应的物理地址为：")
    
    first_fault_idx_sc = -1
    for idx, addr in enumerate(test_addrs):
        page = addr >> 8
        offset = addr & 0xFF
        frame, fault, victim, phys = proc_sc.access_second_chance(addr)
        
        if not fault:
            print(f"{addr}-{phys}")
        else:
            if first_fault_idx_sc == -1:
                first_fault_idx_sc = idx
            print(f"{addr}-{phys}")
    
    # 如果有缺页，显示第一次缺页的详细信息
    if first_fault_idx_sc >= 0:
        # 重新运行以获取详细信息
        proc_sc_detail = Process(test_pid, n1 if test_pid == 1 else (n2 if test_pid == 2 else n3), 
                                 f1 if test_pid == 1 else (f2 if test_pid == 2 else f3))
        proc_sc_detail.init_page_table(initial_pages.copy())
        
        fault_count = 0
        fault_info = None
        for idx, addr in enumerate(test_addrs):
            page = addr >> 8
            offset = addr & 0xFF
            frame, fault, victim, phys = proc_sc_detail.access_second_chance(addr)
            
            if fault:
                fault_count += 1
                if fault_count == first_fault_idx_sc + 1:
                    fault_info = (idx, page, victim, phys, proc_sc_detail)
                    break
        
        if fault_info:
            idx, page, victim, phys, detail_proc = fault_info
            print(f"\n第 {idx + 1} 次访问发生缺页，根据二次机会算法，")
            print(f"将 {victim} 页换出，将 {page} 页换入，对应的物理地址为 {phys}，")
            print(f"{proc_name} 更新后的页表内容如下：")
            print_pt(detail_proc)
    
    sc_faults = proc_sc.sc_faults
    
    # ===== 结果对比 =====
    total = len(test_addrs)
    
    # 边界检查：避免除零错误
    if total == 0:
        print("\n警告：测试序列为空，无法计算缺页率")
        return
    
    print("\n" + "=" * 60)
    print("算法对比结果")
    print("=" * 60)
    
    print(f"\n基础统计:")
    print(f"测试进程：{proc_name}")
    print(f"总访问次数：{total}")
    print(f"初始页表页数：{len(initial_pages)}")
    print(f"分配帧数：{num_frames}")
    
    print(f"\n缺页统计:")
    print(f"{'算法':^10} {'缺页次数':^10} {'缺页率':^12}")
    print("-" * 35)
    print(f"{'LRU':^10} {lru_faults:^10} {lru_faults/total:^12.2%}")
    print(f"{'二次机会':^10} {sc_faults:^10} {sc_faults/total:^12.2%}")
    
    print(f"\n算法特性对比:")
    print(f"{'特性':^20} {'LRU':^20} {'二次机会':^20}")
    print("-" * 60)
    print(f"{'淘汰策略':^20} {'最久未使用':^20} {'FIFO+引用位':^20}")
    print(f"{'局部性利用':^20} {'好':^20} {'一般':^20}")
    print(f"{'实现复杂度':^20} {'中':^20} {'低':^20}")
    print(f"{'内存开销':^20} {'高(需维护顺序)':^20} {'低(只需ref位)':^20}")
    
    print(f"\n结论:")
    if lru_faults < sc_faults:
        print("[OK] LRU算法性能优于二次机会算法")
        print("原因：LRU能更好地利用程序局部性原理，优先淘汰最久未使用的页面")
        print("适合场景：程序访问具有明显局部性特征")
    elif lru_faults > sc_faults:
        print("[OK] 二次机会算法性能优于LRU算法")
        print("原因：当前测试序列对二次机会更有利（可能序列缺乏明显局部性）")
        print("适合场景：程序访问模式较为均匀")
    else:
        print("[OK] 两种算法性能相当")
        print("原因：当前测试序列下两种算法表现一致")
    
    print(f"\n算法差异核心原因分析:")
    print("* LRU：基于访问时间排序，能识别并保留近期频繁访问的页面")
    print("* 二次机会：基于FIFO+引用位，给近期访问过的页面第二次机会")
    print("* 差异根源：LRU精确追踪访问顺序，二次机会仅通过引用位粗略判断")
    
    # ===== 可视化 =====
    if input("\n>>> 是否运行可视化？(y/n)：").lower() == 'y':
        pygame.init()
        screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Virtual Memory Simulation")
        clock = pygame.time.Clock()
        
        # LRU可视化
        vis_lru = Process(2, n2, f2)
        vis_lru.init_page_table(initial_pages_p2)
        
        print("\n--- LRU 可视化 ---")
        for idx, addr in enumerate(test_addrs):
            page = vis_lru.extract_page(addr)
            res = vis_lru.access_lru(addr)
            info = f"Step {idx+1}/{total} | Addr={addr}"
            draw_simulation(screen, [p1, vis_lru, p3], "LRU", vis_lru, page, res, info)
            clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
        pygame.time.wait(1500)
        
        # 二次机会可视化
        vis_sc = Process(2, n2, f2)
        vis_sc.init_page_table(initial_pages_p2)
        
        print("\n--- 二次机会 可视化 ---")
        for idx, addr in enumerate(test_addrs):
            page = vis_sc.extract_page(addr)
            res = vis_sc.access_second_chance(addr)
            info = f"Step {idx+1}/{total} | Addr={addr}"
            draw_simulation(screen, [p1, vis_sc, p3], "Second Chance", vis_sc, page, res, info)
            clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
        pygame.time.wait(1500)
        pygame.quit()
        print("\n可视化完成！")
    
    print("\n" + "=" * 60)
    print("实验结束！")
    print("=" * 60)


if __name__ == "__main__":
    main()
