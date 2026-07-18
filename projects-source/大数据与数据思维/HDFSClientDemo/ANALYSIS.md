# HDFS 客户端操作 — Java API 实践

## 项目概述

基于 Hadoop 3.3.4 完全分布式集群（1主2从），使用 Java API 实现 HDFS 客户端的完整操作。11 个 JUnit 测试用例覆盖了 HDFS 文件系统的全部常用操作。

## 环境配置

Maven 项目（Java 8），依赖 Hadoop 3.3.4 客户端库：

```xml
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-common</artifactId>
    <version>3.3.4</version>
</dependency>
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>3.3.4</version>
</dependency>
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-hdfs</artifactId>
    <version>3.3.4</version>
</dependency>
```

客户端配置 `hdfs-site.xml` 指定默认副本数为 1（开发环境），运行时可通过代码配置覆盖。

## 操作分类

### 1. 目录管理
- **创建目录** `testMkdirs()`：`FileSystem.mkdirs()` 创建多级目录
- **删除目录** `testDelete()`：`FileSystem.delete()` 递归删除

### 2. 文件 CRUD
- **上传** `testUpload()`：`copyFromLocalFile()` 从本地拷贝到 HDFS
- **下载** `testDownload()`：`copyToLocalFile()` 从 HDFS 拷贝到本地
- **重命名** `testRename()`：`FileSystem.rename()` 文件重命名

### 3. IO 流底层操作
- **流式上传** `testUploadByIO()`：`FileInputStream` → `FSDataOutputStream`
- **流式下载** `testDownloadByIO()`：`FSDataInputStream` → `FileOutputStream`

使用 `IOUtils.copyBytes()` 完成流拷贝，手动管理流关闭，理解 HDFS 数据流的底层机制。

### 4. 数据块级操作
- **按块读取** `testReadFileSeek1()` / `testReadFileSeek2()`：通过 `FSDataInputStream.seek()` 定位到指定偏移，验证 HDFS 128MB 块的物理分片特性

### 5. 元数据查询
- **文件详情** `testListFiles()`：递归遍历，输出文件名/大小/权限/所有者
- **根目录状态** `testListStatus()`：判断文件还是目录
- **块位置追踪** `testFileDetailWithBlocks()`：通过 `BlockLocation[]` 获取每个数据块的偏移、长度和所在的 DataNode 主机列表

## 设计决策

### 参数优先级验证
Hadoop 配置有明确的优先级链：代码中 `conf.set()` > 资源文件 `hdfs-site.xml` > 集群默认配置。`testUploadWithPriority()` 通过设置 `dfs.replication=2` 验证了这一优先级，可以在 Web UI 上确认副本数变化。

### JUnit 驱动开发
每个操作封装为独立的 `@Test` 方法，可单独运行。这种设计使得：
- 集群连通性验证只需运行一个测试
- 每个操作可独立调试
- 测试即文档，新开发者通过看测试用例就能理解全部功能

## 关键代码模式

```java
// 标准连接模式
Configuration conf = new Configuration();
FileSystem fs = FileSystem.get(
    new URI("hdfs://192.168.88.100:9000"),
    conf, "root"
);
// ... 操作 ...
fs.close();
```

所有测试用例使用相同的连接创建模式，通过 `FileSystem.get()` 获取文件系统实例。其中参数优先级验证通过提前 `conf.set()` 改写配置项，展示了 Hadoop 配置体系的灵活性。
