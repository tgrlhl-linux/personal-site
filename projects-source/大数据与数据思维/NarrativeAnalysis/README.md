# 叙事计算 —— 基于电影剧本大数据的叙事结构挖掘与分析系统

**课程：** 大数据与数据思维 · 期末大作业
**成员：** 童国睿（数据管道/API/文档）、杨超越（MR/集群）、何锦辉（前端）、李景颖（算法/优化）

## 项目简介
用 Hadoop MapReduce 分析经典电影剧本，提取情感曲线与角色共现网络，推断叙事模式。

## 数据分析流程

```
IMSDb 剧本下载 → 数据清洗(preprocess.py) → 情感分析(Job1) → 情感曲线
                          ↓                     角色共现(Job2) → 共现网络
                   数据管道(data_pipeline.py) 
                     ↙          ↘
               HBase 3表      JSON文件 
                              Flask API → 前端可视化
```

## 数据集（已准备完毕 ✅）

| 类别 | 数量 | 说明 |
|------|------|------|
| 电影剧本 | **17 部** | 已下载并清洗至 data/cleaned/ |
| 情感词典 | **492 词** | 正面 214 + 负面 278，去重后 |
| 清洗后数据 | **80,720 行** | 1,879 场景，14,168 角色行 |
| 后端 API | **6 端点** | Flask REST 服务 |
| HBase 表 | **3 张** | emotion + character_network + narrative_pattern |

## 快速开始

```bash
# 1. 启动集群
cd cluster && docker-compose up -d

# 2. 上传数据到 HDFS
bash scripts/upload_to_hdfs.sh

# 3. 运行 MR Job
cd mr-jobs && bash run.sh

# 4. 启动 API 服务（可选）
pip install flask flask-cors
python api/app.py

# 5. 打开前端
open frontend/index.html
```

## 目录结构
```
NarrativeAnalysis/
├── README.md              ← 本文件，先读这里
├── docs/
│   ├── 分工说明.md         ← ⭐ 每个人的任务清单（必读）
│   └── 童国睿_个人交付说明.md ← ⭐ 童国睿个人贡献全景（必读）
│
├── data/                  ← 数据文件
│   ├── raw_scripts/       ── 原始剧本（17 部）
│   ├── cleaned/           ── 清洗后数据
│   ├── api_data/          ── API 结构化 JSON
│   ├── emotion_dict.csv   ── 情感词典（492 词）
│   └── movie_list.txt     ── 片单与下载指引
│
├── scripts/               ← 脚本
│   ├── download_scripts.py ── ⭐ IMSDb 批量下载器（童国睿）
│   ├── preprocess.py      ── 剧本清洗与格式化
│   ├── data_pipeline.py   ── ⭐ 全链路数据管道（童国睿）
│   ├── hbase_schema.sh    ── ⭐ HBase 建表脚本（童国睿）
│   └── upload_to_hdfs.sh  ── 上传数据到 HDFS
│
├── api/                   ← ⭐ 后端 API 服务（童国睿）
│   ├── app.py             ── Flask REST API（6 端点）
│   └── requirements.txt   ── 依赖清单
│
├── cluster/               ← 集群配置
│   ├── docker-compose.yml ── 3 节点 Docker 集群
│   ├── Dockerfile         ── Hadoop 镜像构建
│   ├── hadoop-config/     ── Hadoop 配置文件
│   └── start-cluster.sh   ── 一键启动
│
├── mr-jobs/               ← ⭐ MapReduce 核心代码
│   ├── pom.xml            ── Maven 项目配置
│   ├── src/main/java/com/narrative/mr/
│   │   ├── Job1_EmotionAnalysis.java   [情感分析]
│   │   └── Job2_CharacterCooccurrence.java  [角色共现]
│   └── run.sh             ── 编译 + 提交脚本
│
└── frontend/              ← 前端可视化
    ├── index.html         ── 单页应用
    └── data/
        └── sample_movie.json  ── 数据格式示例
```

## 依赖环境
- Docker Desktop（或 Docker Engine）
- JDK 8+
- Maven 3.6+
- 现代浏览器（Chrome/Edge）
