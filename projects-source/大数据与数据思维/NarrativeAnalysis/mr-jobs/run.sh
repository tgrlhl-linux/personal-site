#!/bin/bash
# =============================================================
# 编译 → 打包 → 上传数据 → 提交 Job1 → 提交 Job2
# 在 mr-jobs/ 目录下执行
# =============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$PROJECT_DIR")"

echo "=========================================="
echo "叙事计算 - MapReduce 作业流水线"
echo "=========================================="

# Step 1: Maven 编译打包
echo ""
echo "[1/5] Maven 编译打包..."
cd "$PROJECT_DIR"
mvn clean package -DskipTests
echo "  ✅ JAR 包生成完毕"

# Step 2: 确保 HDFS 目录存在
echo ""
echo "[2/5] 初始化 HDFS 目录..."
docker exec master hadoop fs -mkdir -p /user/movie/input
docker exec master hadoop fs -mkdir -p /user/movie/output
echo "  ✅ HDFS 目录就绪"

# Step 3: 上传清洗后的数据
echo ""
echo "[3/5] 上传剧本数据到 HDFS..."
docker exec master hadoop fs -put -f /data/cleaned/*.txt /user/movie/input/ 2>/dev/null || \
    (echo "  ⚠️  本地数据未找到，尝试从 host 复制..." && \
     docker cp "$BASE_DIR/data/cleaned/" master:/tmp/movie_data/ && \
     docker exec master hadoop fs -put -f /tmp/movie_data/*.txt /user/movie/input/)
echo "  ✅ 数据上传完成"

# 上传情感词典到 HDFS（供 DistributedCache 使用）
echo ""
echo "[3b/5] 上传情感词典到 HDFS..."
docker exec master hadoop fs -mkdir -p /user/movie/dict 2>/dev/null
docker exec master hadoop fs -put -f /tmp/emotion_dict.csv /user/movie/dict/emotion_dict.csv 2>/dev/null || \
    (docker cp "$BASE_DIR/data/emotion_dict.csv" master:/tmp/emotion_dict.csv && \
     docker exec master hadoop fs -put -f /tmp/emotion_dict.csv /user/movie/dict/emotion_dict.csv)
echo "  ✅ 情感词典上传完成"
docker exec master hadoop fs -ls /user/movie/input/

# Step 4: 提交 Job1 - 情感分析
echo ""
echo "[4/5] 提交 Job1 - 情感分析..."
JAR_PATH="$PROJECT_DIR/target/narrative-analysis-1.0-SNAPSHOT.jar"
DICT_HDFS="/user/movie/dict/emotion_dict.csv"
# 确保词典已在 HDFS（否则先上传）
docker exec master hadoop fs -test -e "$DICT_HDFS" 2>/dev/null || \
    (docker cp "$BASE_DIR/data/emotion_dict.csv" master:/tmp/emotion_dict.csv && \
     docker exec master hadoop fs -put -f /tmp/emotion_dict.csv "$DICT_HDFS")
# 提交 Job（使用 HDFS 路径的词典，通过 DistributedCache 分发到 Worker）
docker exec master hadoop jar /tmp/narrative.jar \
    com.narrative.mr.Job1_EmotionAnalysis \
    /user/movie/input \
    /user/movie/output/emotion \
    "$DICT_HDFS" 2>&1 || \
    (docker cp "$JAR_PATH" master:/tmp/narrative.jar && \
     docker exec master hadoop jar /tmp/narrative.jar \
         com.narrative.mr.Job1_EmotionAnalysis \
         /user/movie/input \
         /user/movie/output/emotion \
         "$DICT_HDFS")
echo "  ✅ Job1 完成"

# Step 5: 提交 Job2 - 角色共现
echo ""
echo "[5/5] 提交 Job2 - 角色共现..."
docker exec master hadoop jar /tmp/narrative.jar \
    com.narrative.mr.Job2_CharacterCooccurrence \
    /user/movie/input \
    /user/movie/output/cooccur
echo "  ✅ Job2 完成"

# Step 6: 查看结果
echo ""
echo "=========================================="
echo "✅ 全部 Job 完成！结果如下："
echo "=========================================="
echo ""
echo "情感分析结果："
docker exec master hadoop fs -cat /user/movie/output/emotion/part-r-00000 2>/dev/null | head -30
echo ""
echo "角色共现结果："
docker exec master hadoop fs -cat /user/movie/output/cooccur/part-r-00000 2>/dev/null | head -20

# Step 7: 导出结果到本地（供前端使用）
echo ""
echo "导出结果到本地..."
rm -rf "$BASE_DIR/frontend/data/emotion_results" "$BASE_DIR/frontend/data/cooccur_results"
mkdir -p "$BASE_DIR/frontend/data/emotion_results" "$BASE_DIR/frontend/data/cooccur_results"

# 导出情感分析结果
for f in $(docker exec master hadoop fs -ls /user/movie/output/emotion/ 2>/dev/null | grep part- | awk '{print $NF}'); do
    name=$(basename "$f")
    docker exec master hadoop fs -cat "$f" 2>/dev/null > "$BASE_DIR/frontend/data/emotion_results/$name"
done

# 导出角色共现结果
for f in $(docker exec master hadoop fs -ls /user/movie/output/cooccur/ 2>/dev/null | grep part- | awk '{print $NF}'); do
    name=$(basename "$f")
    docker exec master hadoop fs -cat "$f" 2>/dev/null > "$BASE_DIR/frontend/data/cooccur_results/$name"
done

echo "  ✅ 结果已导出到 frontend/data/"
echo ""
echo "打开 frontend/index.html 查看可视化结果！"
