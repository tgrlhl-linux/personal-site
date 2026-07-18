#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧本数据预处理脚本

功能：
1. 读取原始剧本 .txt 文件
2. 去除 HTML 残留、特殊字符、多余空行
3. 分割场景（识别 INT./EXT./SCENE 标记）
4. 保留角色名标记
5. 输出清洗后的文本

用法：
    python preprocess.py
    python preprocess.py --input ../data/raw_scripts/ --output ../data/cleaned/
"""

import os
import re
import argparse

# 场景标题模式
SCENE_PATTERNS = [
    r'^INT\.\s+', r'^EXT\.\s+', r'^INT\./', r'^EXT\./',
    r'^SCENE\s+\d+', r'^INTERIOR\s+', r'^EXTERIOR\s+',
    r'^\d+\.\s+(INT|EXT)',
]

# 需要过滤的行
FILTER_PATTERNS = [
    r'^WWW\.', r'^HTTP', r'^HTTPS', r'^Copyright',
    r'^All Rights', r'^Produced by', r'^Written by',
    r'^Based on', r'^\\s*$',
]

# 角色名模式（全大写，不含标点）
CHAR_PATTERN = r'^[A-Z][A-Z\s\.]{1,30}$'


def is_scene_header(line):
    """判断是否为场景标题"""
    for p in SCENE_PATTERNS:
        if re.match(p, line.strip(), re.IGNORECASE):
            return True
    return False


def should_filter(line):
    """判断是否应该过滤该行"""
    stripped = line.strip()
    if not stripped:
        return True
    for p in FILTER_PATTERNS:
        if re.match(p, stripped, re.IGNORECASE):
            return True
    return False


def clean_text(text):
    """清洗文本：去除多余空格、HTML实体等"""
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\\u[0-9a-fA-F]{4}', '', text)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def preprocess_script(input_path, output_path):
    """处理单个剧本文件"""
    print(f"  处理: {os.path.basename(input_path)}")

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
    except Exception as e:
        print(f"  ⚠️  读取失败 ({e})，尝试 cp1252 编码...")
        with open(input_path, 'r', encoding='cp1252', errors='ignore') as f:
            raw = f.read()

    raw = clean_text(raw)
    lines = raw.split('\n')

    cleaned_lines = []
    scene_count = 0
    char_count = 0
    total_lines = 0

    for line in lines:
        stripped = line.strip()

        if should_filter(line):
            continue

        if is_scene_header(stripped):
            scene_count += 1
            # 场景标题前加空行作为分隔
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            # 用 [SCENE] 标记场景
            cleaned_lines.append(f'[SCENE] {stripped}')
            total_lines += 1
            continue

        if re.match(CHAR_PATTERN, stripped):
            char_count += 1
            cleaned_lines.append(stripped)
            total_lines += 1
            continue

        # 普通台词/叙述行
        cleaned_lines.append(stripped)
        total_lines += 1

    # 写入输出文件
    output_content = '\n'.join(cleaned_lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)

    print(f"  OK 完成: {scene_count} 场景, {char_count} 角色行, {total_lines} 总行 -> {os.path.basename(output_path)}")

    return scene_count, char_count, total_lines


def main():
    parser = argparse.ArgumentParser(description='剧本数据预处理')
    parser.add_argument('--input', '-i', default='../data/raw_scripts/',
                        help='原始剧本目录')
    parser.add_argument('--output', '-o', default='../data/cleaned/',
                        help='清洗后输出目录')
    args = parser.parse_args()

    input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.input))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.output))

    if not os.path.exists(input_dir):
        print(f"❌ 输入目录不存在: {input_dir}")
        print("   请先创建该目录并将 .txt 剧本放进去")
        return

    os.makedirs(output_dir, exist_ok=True)

    total_scenes = 0
    total_chars = 0
    total_lines = 0
    file_count = 0

    for fname in sorted(os.listdir(input_dir)):
        if fname.endswith('.txt'):
            input_path = os.path.join(input_dir, fname)
            output_path = os.path.join(output_dir, fname)
            s, c, l = preprocess_script(input_path, output_path)
            total_scenes += s
            total_chars += c
            total_lines += l
            file_count += 1

    print(f"\n{'='*50}")
    print(f"✅ 预处理完成！")
    print(f"   处理文件: {file_count} 个")
    print(f"   总场景数: {total_scenes}")
    print(f"   总角色行: {total_chars}")
    print(f"   总行数:   {total_lines}")
    print(f"   输出目录: {output_dir}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
