#!/bin/bash
# =============================================================
# 上传清洗后的数据到 HDFS
# 用法: bash upload_to_hdfs.sh
# 前提: Docker 集群已启动
# =============================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLEANED_DIR="$BASE_DIR/data/cleaned"

echo "=========================================="
echo "上传剧本数据到 HDFS"
echo "=========================================="

# 检查 cleaned 目录
if [ ! -d "$CLEANED_DIR" ] || [ -z "$(ls -A "$CLEANED_DIR" 2>/dev/null)" ]; then
    echo "❌ 未找到清洗后的数据，请先运行 preprocess.py"
    echo "   python scripts/preprocess.py"
    exit 1
fi

echo "数据目录: $CLEANED_DIR"
echo "文件列表:"
ls -la "$CLEANED_DIR"/*.txt 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}' || true

# 确保 HDFS 目录存在
echo ""
echo "创建 HDFS 目录..."
docker exec master hadoop fs -mkdir -p /user/movie/input
docker exec master hadoop fs -mkdir -p /user/movie/output/emotion
docker exec master hadoop fs -mkdir -p /user/movie/output/cooccur
echo "  ✅ HDFS 目录就绪"

# 上传数据
echo ""
echo "上传数据..."
# 方法1：通过 Docker cp + HDFS put
docker exec master mkdir -p /tmp/upload_data
for f in "$CLEANED_DIR"/*.txt; do
    fname=$(basename "$f")
    docker cp "$f" master:/tmp/upload_data/"$fname"
    echo "  复制: $fname"
done
docker exec master hadoop fs -put -f /tmp/upload_data/*.txt /user/movie/input/
echo "  ✅ HDFS put 完成"

# 验证
echo ""
echo "验证上传结果:"
docker exec master hadoop fs -ls /user/movie/input/
total=$(docker exec master hadoop fs -count /user/movie/input/ 2>/dev/null | awk '{print $2}')
echo ""
echo "✅ 上传完成！共上传 $total 个文件到 /user/movie/input/"
echo ""
echo "现在可以提交 MR 任务了:"
echo "   cd mr-jobs && bash run.sh"
