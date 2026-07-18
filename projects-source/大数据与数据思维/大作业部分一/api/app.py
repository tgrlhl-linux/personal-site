#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
叙事计算 — Flask 后端 API 服务

对应设计文档：
- 童国睿 任务④ 后端 API 服务开发
- 提供 RESTful 接口供前端查询情感曲线、角色共现、叙事模式

用法：
    pip install flask flask-cors
    python api/app.py          # 启动服务 (默认 http://localhost:5000)
    python api/app.py --port 8080
"""

import os
import json
import argparse
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'api_data')
ALL_MOVIES_PATH = os.path.join(DATA_DIR, 'all_movies.json')

app = Flask(__name__)
CORS(app)


# =============================================================
# 数据加载
# =============================================================
def load_all_movies():
    """加载所有电影数据"""
    if not os.path.exists(ALL_MOVIES_PATH):
        return {'movies': []}
    with open(ALL_MOVIES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_movie_by_id(movie_id):
    """按 ID 获取单部电影数据"""
    mpath = os.path.join(DATA_DIR, f"{movie_id}.json")
    if os.path.exists(mpath):
        with open(mpath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# =============================================================
# API 路由
# =============================================================

@app.route('/')
def index():
    """API 根路径"""
    return jsonify({
        'name': '叙事计算 API',
        'version': '1.0',
        'endpoints': {
            '/movies': 'GET - 获取所有电影列表',
            '/movies/<id>': 'GET - 获取单部电影完整数据',
            '/movies/<id>/emotion': 'GET - 获取电影情感曲线',
            '/movies/<id>/cooccurrence': 'GET - 获取角色共现数据',
            '/stats': 'GET - 数据集统计信息',
        }
    })


@app.route('/movies', methods=['GET'])
def list_movies():
    """获取所有电影基本信息列表"""
    data = load_all_movies()
    movies = []
    for m in data.get('movies', []):
        movies.append({
            'id': m['id'],
            'name': m['name'],
            'total_scenes': m['total_scenes'],
            'total_characters': m['total_characters'],
        })
    return jsonify({'count': len(movies), 'movies': movies})


@app.route('/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    """获取单部电影完整分析数据"""
    movie = get_movie_by_id(movie_id)
    if movie is None:
        return jsonify({'error': f'Movie not found: {movie_id}'}), 404
    return jsonify(movie)


@app.route('/movies/<movie_id>/emotion', methods=['GET'])
def get_emotion_curve(movie_id):
    """获取电影情感曲线数据"""
    movie = get_movie_by_id(movie_id)
    if movie is None:
        return jsonify({'error': f'Movie not found: {movie_id}'}), 404

    scenes = movie.get('scenes', [])
    emotion_curve = [{
        'scene': s['scene'],
        'name': s['name'],
        'positive': s['pos'],
        'negative': s['neg'],
        'net_emotion': s['net'],
    } for s in scenes]

    # 计算曲线统计
    net_values = [s['net'] for s in scenes]
    avg_net = sum(net_values) / max(len(net_values), 1)
    max_net = max(net_values) if net_values else 0
    min_net = min(net_values) if net_values else 0

    # 检测叙事转折点（ECR 简化版）
    turning_points = []
    for i in range(1, len(scenes) - 1):
        prev_net = scenes[i - 1]['net']
        curr_net = scenes[i]['net']
        next_net = scenes[i + 1]['net']
        ecr = abs(curr_net - prev_net) + abs(next_net - curr_net)
        if ecr > 0.05:  # 阈值过滤
            turning_points.append({
                'scene': scenes[i]['scene'],
                'name': scenes[i]['name'],
                'ecr': round(ecr, 6)
            })

    return jsonify({
        'movie_id': movie_id,
        'movie_name': movie['name'],
        'total_scenes': movie['total_scenes'],
        'emotion_curve': emotion_curve,
        'stats': {
            'avg_net_emotion': round(avg_net, 6),
            'max_net_emotion': round(max_net, 6),
            'min_net_emotion': round(min_net, 6),
        },
        'turning_points': turning_points[:10],  # Top-10 转折点
    })


@app.route('/movies/<movie_id>/cooccurrence', methods=['GET'])
def get_cooccurrence(movie_id):
    """获取角色共现数据"""
    movie = get_movie_by_id(movie_id)
    if movie is None:
        return jsonify({'error': f'Movie not found: {movie_id}'}), 404

    cooc = movie.get('cooccurrences', [])
    return jsonify({
        'movie_id': movie_id,
        'movie_name': movie['name'],
        'total_pairs': len(cooc),
        'cooccurrences': cooc,
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """数据集统计信息"""
    data = load_all_movies()
    movies = data.get('movies', [])

    if not movies:
        return jsonify({
            'total_movies': 0,
            'total_scenes': 0,
            'total_characters': 0,
            'total_cooccurrence_pairs': 0,
        })

    total_scenes = sum(m['total_scenes'] for m in movies)
    total_chars = sum(m['total_characters'] for m in movies)
    total_pairs = sum(len(m['cooccurrences']) for m in movies)

    return jsonify({
        'total_movies': len(movies),
        'total_scenes': total_scenes,
        'total_characters': total_chars,
        'total_cooccurrence_pairs': total_pairs,
        'movie_list': [{'id': m['id'], 'name': m['name']} for m in movies],
    })


# =============================================================
# 启动服务
# =============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='叙事计算 API 服务')
    parser.add_argument('--port', '-p', type=int, default=5000, help='端口号')
    parser.add_argument('--debug', '-d', action='store_true', help='调试模式')
    args = parser.parse_args()

    # 确保数据已生成
    if not os.path.exists(DATA_DIR) or not os.path.exists(ALL_MOVIES_PATH):
        print("[API 数据未生成，请先运行]")
        print("   python scripts/data_pipeline.py --pipeline api")
        print(f"   或确保 {ALL_MOVIES_PATH} 存在")
    else:
        with open(ALL_MOVIES_PATH, 'r') as f:
            count = len(json.load(f).get('movies', []))
        print(f"[已加载 {count} 部电影数据]")

    print(f"\n[叙事计算 API 启动] http://localhost:{args.port}")
    print(f"   API 文档: http://localhost:{args.port}/")
    print(f"   电影列表: http://localhost:{args.port}/movies")
    print(f"   数据统计: http://localhost:{args.port}/stats")
    print(f"   单部电影: http://localhost:{args.port}/movies/The_Matrix")
    print(f"   情感曲线: http://localhost:{args.port}/movies/The_Matrix/emotion")
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)
