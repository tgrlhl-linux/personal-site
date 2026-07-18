#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管道：预处理 → HBase 导入 → 后端 API 数据准备

对应设计文档：
- 童国睿 任务③ HBase 建表与数据写入
- 童国睿 任务② 预处理 Pipeline + HDFS 导入

用法：
    # 完整流程（预处理 + 生成分析数据）
    python data_pipeline.py --pipeline full

    # 仅生成 API 数据（从清洗结果 + 情感词典生成结构化 JSON）
    python data_pipeline.py --pipeline api

    # 仅导入 HBase（依赖集群运行）
    python data_pipeline.py --pipeline hbase
"""

import os
import re
import csv
import json
import argparse
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')
DICT_PATH = os.path.join(DATA_DIR, 'emotion_dict.csv')
OUTPUT_DIR = os.path.join(DATA_DIR, 'api_data')


# =============================================================
# 1. 加载情感词典
# =============================================================
def load_emotion_dict(path):
    """加载情感词典，返回 {word: (positive, negative)}"""
    word_dict = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = row['word'].strip().lower()
            if not w or w.startswith('#'):
                continue
            word_dict[w] = (int(row['positive']), int(row['negative']))
    return word_dict


# =============================================================
# 2. 分析单部剧本
# =============================================================
def analyze_script(filepath, movie_id, movie_name, word_dict):
    """分析单部剧本，返回结构化的情感 + 角色数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    scenes = []
    current_scene = {'scene_id': 0, 'name': 'UNKNOWN', 'lines': [], 'characters': set()}
    scene_counter = 0
    all_characters = set()
    char_scene_map = defaultdict(set)  # char -> set of scene_ids
    char_pos = defaultdict(int)
    char_neg = defaultdict(int)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[SCENE]'):
            # 保存上一场景
            if current_scene['lines']:
                scenes.append(current_scene)
            scene_counter += 1
            current_scene = {
                'scene_id': scene_counter,
                'name': stripped.replace('[SCENE] ', '').strip(),
                'lines': [],
                'characters': set()
            }
        elif stripped and re.match(r'^[A-Z][A-Z\s\.]{1,30}$', stripped):
            char_name = stripped.strip()
            all_characters.add(char_name)
            current_scene['characters'].add(char_name)
            char_scene_map[char_name].add(current_scene['scene_id'])
        else:
            current_scene['lines'].append(stripped)

    # 保存最后一幕
    if current_scene['lines']:
        scenes.append(current_scene)

    # 如果没有场景标记，按固定窗口分割（每 50 行一个场景）
    if len(scenes) <= 1:
        scenes = []
        window_size = 50
        for i in range(0, len(lines), window_size):
            window_lines = lines[i:i + window_size]
            scene_counter += 1
            chars_in_window = set()
            for line in window_lines:
                stripped = line.strip()
                if stripped and re.match(r'^[A-Z][A-Z\s\.]{1,30}$', stripped):
                    chars_in_window.add(stripped.strip())
                    char_scene_map[stripped.strip()].add(scene_counter)
            scenes.append({
                'scene_id': scene_counter,
                'name': f'WINDOW_{scene_counter}',
                'lines': window_lines,
                'characters': chars_in_window
            })

    # 情感分析
    emotion_results = []
    for scene in scenes:
        pos_count = 0
        neg_count = 0
        total_words = 0
        for line in scene['lines']:
            words = line.lower().split()
            total_words += len(words)
            for w in words:
                w_clean = re.sub(r'[^a-z]', '', w)
                if w_clean in word_dict:
                    p, n = word_dict[w_clean]
                    pos_count += p
                    neg_count += n

        net_emotion = round((pos_count - neg_count) / max(total_words, 1), 6)
        emotion_results.append({
            'scene': scene['scene_id'],
            'name': scene['name'],
            'pos': pos_count,
            'neg': neg_count,
            'net': net_emotion
        })

    # 角色共现
    char_list = sorted(all_characters)
    cooccur = defaultdict(int)
    for scene in scenes:
        chars = list(scene['characters'])
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                pair = tuple(sorted([chars[i], chars[j]]))
                cooccur[pair] += 1

    cooccur_results = [
        {'charA': a, 'charB': b, 'count': c}
        for (a, b), c in sorted(cooccur.items(), key=lambda x: -x[1])
    ]

    return {
        'id': movie_id,
        'name': movie_name,
        'total_scenes': len(scenes),
        'total_characters': len(all_characters),
        'scenes': emotion_results,
        'cooccurrences': cooccur_results[:30]  # Top-30
    }


# =============================================================
# 3. 生成所有电影的 API 数据
# =============================================================
def generate_api_data(word_dict):
    """分析所有清洗后的剧本，生成前端 API 可用的 JSON 数据集"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    movies_data = []
    for fname in sorted(os.listdir(CLEANED_DIR)):
        if not fname.endswith('.txt'):
            continue

        filepath = os.path.join(CLEANED_DIR, fname)
        movie_id = fname.replace('.txt', '')
        movie_name = movie_id.replace('_', ' ')

        print(f"  分析: {fname}")
        result = analyze_script(filepath, movie_id, movie_name, word_dict)
        movies_data.append(result)

    # 写入单文件（前端用）
    output_path = os.path.join(OUTPUT_DIR, 'all_movies.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'movies': movies_data}, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ 写入: {output_path}")

    # 按电影拆分（API 用）
    for movie in movies_data:
        mpath = os.path.join(OUTPUT_DIR, f"{movie['id']}.json")
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(movie, f, ensure_ascii=False, indent=2)

    # 统计
    total_scenes = sum(m['total_scenes'] for m in movies_data)
    total_chars = sum(m['total_characters'] for m in movies_data)
    print(f"\n{'='*50}")
    print(f"✅ API 数据生成完成！")
    print(f"   电影数:     {len(movies_data)}")
    print(f"   总场景数:   {total_scenes}")
    print(f"   总角色数:   {total_chars}")
    print(f"   输出目录:   {OUTPUT_DIR}")
    print(f"{'='*50}")

    return movies_data


# =============================================================
# 4. HBase 数据写入（可选，需要 HBase 集群）
# =============================================================
def write_to_hbase(movies_data):
    """将分析结果写入 HBase（3 张表）"""
    try:
        import happybase
        connection = happybase.Connection('localhost', 9090)
        print("\n  连接 HBase 成功")
    except ImportError:
        print("\n  ⚠️ happybase 未安装，跳过 HBase 写入")
        print(f"     pip install happybase")
        print(f"     或使用文件数据: python data_pipeline.py --pipeline api")
        return
    except Exception as e:
        print(f"\n  ⚠️ HBase 连接失败: {e}")
        print(f"     请确保 HBase Thrift 服务已启动")
        return

    # 写 movie_emotion 表
    table_emotion = connection.table('movie_emotion')
    table_network = connection.table('character_network')
    table_pattern = connection.table('narrative_pattern')

    for movie in movies_data:
        mid = movie['id']
        print(f"  写入 HBase: {mid}")

        # movie_emotion: 场景情感
        scene_data = {}
        for s in movie['scenes']:
            key = f"scene_{s['scene']:04d}"
            scene_data[key] = json.dumps(s)
        table_emotion.put(mid, {
            'emotion:scenes': json.dumps(movie['scenes']),
            'meta:name': movie['name'],
            'meta:scenes': str(movie['total_scenes']),
            'meta:characters': str(movie['total_characters']),
        })

        # character_network: 角色共现
        cooc_data = {}
        for c in movie['cooccurrences']:
            pair_key = f"{c['charA']}#{c['charB']}"
            cooc_data[f"cooccur:{pair_key}"] = str(c['count'])
        table_network.put(mid, cooc_data)

        # narrative_pattern: 叙事模式（简化版）
        emotion_series = [s['net'] for s in movie['scenes']]
        mean_emo = sum(emotion_series) / max(len(emotion_series), 1)
        std_emo = (sum((e - mean_emo) ** 2 for e in emotion_series) / max(len(emotion_series), 1)) ** 0.5
        pattern = {
            'acts': len(movie['scenes']) // 10 + 1,
            'emotion_mean': round(mean_emo, 6),
            'emotion_std': round(std_emo, 6),
            'scene_count': movie['total_scenes'],
            'char_count': movie['total_characters'],
        }
        table_pattern.put(mid, {
            'features:fingerprint': json.dumps(pattern),
            'acts:count': str(pattern['acts']),
            'cluster:label': 'undetermined',
        })

    connection.close()
    print(f"\n  ✅ HBase 写入完成！共 {len(movies_data)} 部电影")


# =============================================================
# 5. Main
# =============================================================
def main():
    parser = argparse.ArgumentParser(description='叙事计算数据管道')
    parser.add_argument('--pipeline', '-p', default='api',
                        choices=['full', 'api', 'hbase'],
                        help='运行模式: full(全部) / api(生成JSON) / hbase(写入HBase)')
    args = parser.parse_args()

    print(f"{'='*50}")
    print(f"叙事计算数据管道 (Pipeline)")
    print(f"模式: {args.pipeline}")
    print(f"{'='*50}")

    # 加载词典
    print("\n[1/3] 加载情感词典...")
    word_dict = load_emotion_dict(DICT_PATH)
    print(f"  词典加载: {len(word_dict)} 词")

    # 分析剧本 + 生成 API 数据
    print("\n[2/3] 分析剧本数据...")
    movies_data = generate_api_data(word_dict)

    # HBase 写入
    if args.pipeline in ('full', 'hbase'):
        print("\n[3/3] 写入 HBase...")
        write_to_hbase(movies_data)
    else:
        print(f"\n[3/3] 跳过 (API 模式不写 HBase)")
        print(f"  如需写入 HBase: python data_pipeline.py --pipeline hbase")

    print(f"\n{'='*50}")
    print(f"✅ Pipeline 完成！")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
