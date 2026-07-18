#!/bin/bash
# =============================================================
# 叙事计算 - Docker Hadoop 集群一键启动脚本
# 用法: bash start-cluster.sh
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 叙事计算 Hadoop 集群启动"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 未找到 Docker，请先安装 Docker Desktop"
    echo "   下载: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ 未找到 docker compose 命令"
    echo "   请更新 Docker Desktop 或安装 docker-compose-plugin"
    exit 1
fi

echo "Docker 版本: $(docker --version)"
echo ""

# 构建并启动
echo "构建 Docker 镜像（首次需要 3-5 分钟）..."
docker compose build
echo "  ✅ 构建完成"

echo ""
echo "启动集群..."
docker compose up -d
echo "  ✅ 容器已启动"

# 等待服务就绪
echo ""
echo "等待 HDFS 服务就绪..."
sleep 10

# 验证
echo ""
echo "验证集群状态..."
echo ""
echo "容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "HDFS 状态:"
if docker exec master hdfs dfsadmin -report 2>/dev/null | head -5; then
    echo "  ✅ HDFS 正常"
else
    echo "  ⚠️  HDFS 可能还未完全启动，等待 10 秒..."
    sleep 10
    docker exec master hdfs dfsadmin -report 2>/dev/null | head -5 || true
fi

echo ""
echo "YARN 状态:"
if docker exec master yarn node -list 2>/dev/null | head -5; then
    echo "  ✅ YARN 正常"
else
    echo "  ⚠️  YARN 可能还未完全启动"
fi

echo ""
echo "=========================================="
echo "✅ 集群启动完成！"
echo "=========================================="
echo ""
echo "Web 管理界面:"
echo "  HDFS NameNode:  http://localhost:9870"
echo "  YARN ResourceManager: http://localhost:8088"
echo ""
echo "常用命令:"
echo "  进入 master: docker exec -it master bash"
echo "  HDFS 列表:   docker exec master hadoop fs -ls /"
echo "  停止集群:    docker compose down"
echo "  查看日志:    docker compose logs -f master"
