#!/bin/bash
# =============================================================
# HBase 表结构初始化脚本
# 对应设计文档 5.2 节 HBase 表设计
# 用法: docker exec hbase-master hbase shell /tmp/hbase_schema.hbase
# =============================================================

echo "=========================================="
echo "初始化 HBase 表结构"
echo "=========================================="

# =============================================
# 表 1: movie_emotion — 各场景情感向量
# RowKey: movie_id (String)
# CF: emotion — scene_seq → vector (JSON)
# CF: meta    — title, year, genre, director
# =============================================
echo "创建表: movie_emotion..."
echo "create 'movie_emotion', 'emotion', 'meta'" | hbase shell
echo "  ✅ movie_emotion 就绪"

# =============================================
# 表 2: character_network — 角色共现矩阵
# RowKey: movie_id (String)
# CF: cooccur — charA#charB → count
# CF: role    — char_name → appearances
# =============================================
echo "创建表: character_network..."
echo "create 'character_network', 'cooccur', 'role'" | hbase shell
echo "  ✅ character_network 就绪"

# =============================================
# 表 3: narrative_pattern — 叙事模式
# RowKey: movie_id (String)
# CF: acts  — boundaries, duration_ratio
# CF: features — fingerprint_vector (JSON)
# CF: cluster — label, silhouette
# =============================================
echo "创建表: narrative_pattern..."
echo "create 'narrative_pattern', 'acts', 'features', 'cluster'" | hbase shell
echo "  ✅ narrative_pattern 就绪"

echo ""
echo "=========================================="
echo "✅ HBase 表初始化完成！共 3 张表"
echo "=========================================="
echo "  movie_emotion      — 场景情感向量"
echo "  character_network  — 角色共现网络"
echo "  narrative_pattern  — 叙事模式特征"
echo "=========================================="
