# 大数据叙事分析系统

## 项目概述

基于 Hadoop + HBase 的大规模电影剧本叙事分析系统。对多部电影剧本进行情感计算、角色网络分析和叙事模式提取，结果存入 HBase 并通过 Flask API 暴露给前端可视化展示。这是一个完整的大数据应用 demo：数据管道 -> 分布式存储 -> API 服务 -> Web 前端。

## 架构设计

系统包含五个组件：

数据管道（data_pipeline.py）：从清洗后的剧本文件出发，加载情感词典，逐剧本分析场景情感、角色共现和叙事模式。结果以 JSON 格式输出到 api_data/ 目录，同时支持写入 HBase。

HBase 存储（hbase_schema.sh）：创建三张表——movie_emotion（场景情感序列）、character_network（角色共现矩阵）、narrative_pattern（叙事模式指纹）。表结构围绕列族设计，每张表的 RowKey 为电影 ID。

Flask API（api/app.py）：提供 RESTful 接口，从 HBase 读取分析数据返回 JSON 或直接读取本地 JSON 文件作为 fallback。支持按电影 ID 查询、列表查询等端点。

前端展示（frontend/index.html）：可视化展示情感曲线、角色关系网络和叙事模式对比，作为数据分析结果的直观呈现。

集群启动（cluster/start-cluster.sh）：一键启动 Hadoop + HBase 集群的脚本，支持 Docker 环境。

## 技术亮点

多级数据管道设计：Pipeline 支持三种模式（full/api/hbase），数据经过预处理 -> 情感分析 -> 结构化 JSON -> HBase 导入四个阶段。每一阶段产物可独立使用，JSON 文件可直接供前端展示，HBase 存储用于大规模查询。

情感时序分析：逐场景计算净情感值（pos-neg）/总词数，形成贯穿全剧的情感变化曲线。用于分析剧本的叙事节奏——情感曲线在剧情高潮、反转和结尾阶段呈现明显波动。

叙事模式聚类准备：每部电影提取情感均值、标准差、场景数、角色数等特征构成叙事指纹，后续可基于这些向量进行剧本聚类分析，发现叙事风格的相似性。

## 设计决策

HBase 列族设计遵循查询模式驱动原则：emotion 列族支持场景级情感范围扫描，cooccur 列族支持角色对查询，features 列族支持叙事特征向量提取。三张表分别服务于不同的分析视角，避免单表列族过多带来的性能问题。

Flask API 同时支持 HBase 和本地 JSON 两种数据源，使得前端开发可以不依赖 Hadoop 集群，本地 JSON 作为开发数据源，HBase 作为生产数据源。

## 关键代码解读

```python
def analyze_script(filepath, movie_id, movie_name, word_dict):
    # 场景分割 -> 情感计算 -> 角色共现
    for line in lines:
        if stripped.startswith('[SCENE]'):
            # 场景切换
        elif re.match(r'^[A-Z][A-Z\s\.]{1,30}$', stripped):
            # 角色识别
    # 情感归一化
    net_emotion = round((pos_count - neg_count) / max(total_words, 1), 6)
```

剧本分析引擎同时完成场景分割、角色识别和情感计算三项任务。一次遍历完成所有分析，时间复杂度 O(n) 且空间占用仅与角色数量和场景数相关，与剧本长度无关。
