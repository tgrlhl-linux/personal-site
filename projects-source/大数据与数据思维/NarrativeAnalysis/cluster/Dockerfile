FROM openjdk:8-jdk-slim

LABEL description="Hadoop 3.3.6 单节点镜像（叙事计算项目）"
LABEL version="1.0"

# 安装依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        openssh-server \
        openssh-client \
        rsync \
        curl \
        net-tools \
        python3 \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 Hadoop
ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

RUN wget -q https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz -O /tmp/hadoop.tar.gz && \
    tar -xzf /tmp/hadoop.tar.gz -C /opt/ && \
    mv /opt/hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm /tmp/hadoop.tar.gz

# 配置 SSH
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys

# SSH 配置（允许 root 登录）
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 环境变量
ENV JAVA_HOME=/usr/local/openjdk-8
ENV HDFS_NAMENODE_USER=root
ENV HDFS_DATANODE_USER=root
ENV HDFS_SECONDARYNAMENODE_USER=root
ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root

# 启动脚本
COPY cluster/hadoop-config/* $HADOOP_CONF_DIR/

WORKDIR /root
CMD ["bash"]
