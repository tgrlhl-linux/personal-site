-- =============================================
-- 数据库创建
-- =============================================
CREATE DATABASE IF NOT EXISTS immersive_script_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE immersive_script_db;

-- =============================================
-- 1. 用户表 (User)
-- =============================================
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一标识',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '登录密码（加密存储）',
    phone VARCHAR(11) NOT NULL UNIQUE COMMENT '手机号',
    email VARCHAR(100) NULL COMMENT '电子邮箱',
    nickname VARCHAR(50) NOT NULL COMMENT '用户昵称/姓名',
    avatar_url VARCHAR(255) NULL COMMENT '头像URL',
    role_type TINYINT NOT NULL DEFAULT 0 COMMENT '角色类型：0-游客 1-运营 2-NPC 3-管理员',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-正常 1-禁用',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- =============================================
-- 2. 剧本表 (Script)
-- =============================================
CREATE TABLE Script (
    script_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '剧本唯一标识',
    name VARCHAR(100) NOT NULL COMMENT '剧本名称',
    description TEXT NULL COMMENT '剧本描述/简介',
    difficulty TINYINT NOT NULL DEFAULT 1 COMMENT '难度等级：1-5',
    duration INT NOT NULL COMMENT '预计时长（分钟）',
    min_players INT NOT NULL DEFAULT 1 COMMENT '最少参与人数',
    max_players INT NOT NULL COMMENT '最多参与人数',
    cover_url VARCHAR(255) NULL COMMENT '封面图片URL',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-草稿 1-已上架 2-已下架',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='剧本表';

-- =============================================
-- 3. 角色表 (Role)
-- =============================================
CREATE TABLE Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色唯一标识',
    script_id INT NOT NULL COMMENT '所属剧本ID',
    name VARCHAR(50) NOT NULL COMMENT '角色名称',
    description TEXT NULL COMMENT '角色描述/背景故事',
    avatar_url VARCHAR(255) NULL COMMENT '角色头像URL',
    is_key_role TINYINT NOT NULL DEFAULT 0 COMMENT '是否关键角色：0-否 1-是',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序编号',
    CONSTRAINT fk_role_script FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- =============================================
-- 4. 线索表 (Clue)
-- =============================================
CREATE TABLE Clue (
    clue_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '线索唯一标识',
    script_id INT NOT NULL COMMENT '所属剧本ID',
    name VARCHAR(100) NOT NULL COMMENT '线索名称',
    content TEXT NOT NULL COMMENT '线索内容',
    clue_type TINYINT NOT NULL DEFAULT 0 COMMENT '线索类型：0-文字 1-图片 2-音频 3-视频',
    media_url VARCHAR(255) NULL COMMENT '多媒体素材URL',
    trigger_type TINYINT NOT NULL DEFAULT 0 COMMENT '触发方式：0-打卡到达 1-上一线索完成 2-NPC互动',
    trigger_id INT NULL COMMENT '触发条件关联ID（打卡点ID或上一线索ID）',
    sequence_num INT NOT NULL COMMENT '线索在链中的顺序编号',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序编号',
    CONSTRAINT fk_clue_script FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='线索表';

-- =============================================
-- 5. 打卡点表 (CheckPoint)
-- =============================================
CREATE TABLE CheckPoint (
    point_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '打卡点唯一标识',
    name VARCHAR(100) NOT NULL COMMENT '点位名称',
    latitude DECIMAL(10, 7) NOT NULL COMMENT 'GPS纬度坐标',
    longitude DECIMAL(10, 7) NOT NULL COMMENT 'GPS经度坐标',
    ar_content_url VARCHAR(255) NULL COMMENT 'AR交互内容URL',
    binding_clue_id INT NULL COMMENT '绑定的线索ID',
    is_required TINYINT NOT NULL DEFAULT 0 COMMENT '是否必打卡点：0-否 1-是',
    description TEXT NULL COMMENT '点位描述/介绍',
    CONSTRAINT fk_cp_clue FOREIGN KEY (binding_clue_id) REFERENCES Clue(clue_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡点表';

-- =============================================
-- 6. 场次表 (Session)
-- =============================================
CREATE TABLE `Session` (
    session_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '场次唯一标识',
    script_id INT NOT NULL COMMENT '所属剧本ID',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME NULL COMMENT '预计结束时间',
    max_players INT NOT NULL COMMENT '最大参与人数',
    current_players INT NOT NULL DEFAULT 0 COMMENT '当前参与人数',
    price DECIMAL(10, 2) NOT NULL COMMENT '价格',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待开始 1-进行中 2-已结束 3-已取消',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_session_script FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场次表';

-- =============================================
-- 7. 订单表 (Order)
-- =============================================
CREATE TABLE `Order` (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单唯一标识',
    user_id INT NOT NULL COMMENT '用户ID',
    session_id INT NOT NULL COMMENT '场次ID',
    role_id INT NULL COMMENT '所选角色ID',
    amount DECIMAL(10, 2) NOT NULL COMMENT '订单金额',
    payment_status TINYINT NOT NULL DEFAULT 0 COMMENT '支付状态：0-未支付 1-已支付 2-已退款',
    payment_time DATETIME NULL COMMENT '支付时间',
    order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES User(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_session FOREIGN KEY (session_id) REFERENCES `Session`(session_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_role FOREIGN KEY (role_id) REFERENCES Role(role_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- =============================================
-- 8. NPC排班表 (NpcSchedule)
-- =============================================
CREATE TABLE NpcSchedule (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '排班唯一标识',
    npc_id INT NOT NULL COMMENT 'NPC用户ID',
    session_id INT NOT NULL COMMENT '场次ID',
    duty_role VARCHAR(50) NOT NULL COMMENT '岗位职责（DM/扮演角色名）',
    schedule_date DATE NOT NULL COMMENT '排班日期',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-已排班 1-已签到 2-已完成 3-缺勤',
    notes TEXT NULL COMMENT '备注/交接事项',
    CONSTRAINT fk_npc_user FOREIGN KEY (npc_id) REFERENCES User(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_npc_session FOREIGN KEY (session_id) REFERENCES `Session`(session_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uk_npc_session UNIQUE (npc_id, session_id, duty_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='NPC排班表';

-- =============================================
-- 9. 游玩进度表 (PlayerProgress)
-- =============================================
CREATE TABLE PlayerProgress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '进度唯一标识',
    user_id INT NOT NULL COMMENT '游客用户ID',
    session_id INT NOT NULL COMMENT '场次ID',
    current_clue_seq INT NOT NULL DEFAULT 0 COMMENT '当前进行到的线索序号',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-进行中 1-已完成 2-已退出',
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始游玩时间',
    last_active_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后活动时间',
    complete_time DATETIME NULL COMMENT '完成时间',
    CONSTRAINT fk_progress_user FOREIGN KEY (user_id) REFERENCES User(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_progress_session FOREIGN KEY (session_id) REFERENCES `Session`(session_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uk_user_session UNIQUE (user_id, session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='游玩进度表';

-- =============================================
-- 10. 评价表 (Review)
-- =============================================
CREATE TABLE Review (
    review_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '评价唯一标识',
    user_id INT NOT NULL COMMENT '用户ID',
    session_id INT NOT NULL COMMENT '场次ID',
    script_id INT NOT NULL COMMENT '剧本ID',
    rating TINYINT NOT NULL COMMENT '评分：1-5星',
    content TEXT NULL COMMENT '评价文字内容',
    image_urls TEXT NULL COMMENT '图片URL（JSON数组）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评价时间',
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES User(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_review_session FOREIGN KEY (session_id) REFERENCES `Session`(session_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_review_script FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评价表';

-- =============================================
-- 验证：查看所有建好的表
-- =============================================
SHOW TABLES;

ALTER TABLE User
ADD CONSTRAINT chk_user_role_type
CHECK (role_type IN (0, 1, 2, 3));

ALTER TABLE Review
ADD CONSTRAINT chk_review_rating
CHECK (rating >= 1 AND rating <= 5);

ALTER TABLE Script
ADD CONSTRAINT chk_script_difficulty
CHECK (difficulty >= 1 AND difficulty <= 5);

-- 为常用查询字段创建索引，提升查询性能
CREATE INDEX idx_user_role_type ON User(role_type);
CREATE INDEX idx_order_user_id ON `Order`(user_id);
CREATE INDEX idx_order_session_id ON `Order`(session_id);
CREATE INDEX idx_order_payment_status ON `Order`(payment_status);
CREATE INDEX idx_session_script_id ON `Session`(script_id);
CREATE INDEX idx_session_start_time ON `Session`(start_time);
CREATE INDEX idx_review_script_id ON Review(script_id);
CREATE INDEX idx_review_rating ON Review(rating);
CREATE INDEX idx_clue_script_id ON Clue(script_id);
CREATE INDEX idx_clue_sequence ON Clue(script_id, sequence_num);
CREATE INDEX idx_progress_user_session ON PlayerProgress(user_id, session_id);
CREATE INDEX idx_npc_schedule_date ON NpcSchedule(schedule_date);

-- =============================================
-- 插入测试数据（每张主表不少于10条记录）
-- =============================================

-- =============================================
-- 4.1 用户数据（10条）
-- =============================================
INSERT INTO User (username, password, phone, nickname, role_type) VALUES
('zhangsan',  'e10adc3949ba59abbe56e057f20f883e', '13800138001', '张三',   0),
('lisi',      'e10adc3949ba59abbe56e057f20f883e', '13800138002', '李四',   0),
('wangwu',    'e10adc3949ba59abbe56e057f20f883e', '13800138003', '王五',   0),
('opera_li',  'e10adc3949ba59abbe56e057f20f883e', '13900139001', '李运营', 1),
('npc_zhou',  'e10adc3949ba59abbe56e057f20f883e', '13700137001', '周NPC',  2),
('npc_wu',    'e10adc3949ba59abbe56e057f20f883e', '13700137002', '吴NPC',  2),
('admin',     'e10adc3949ba59abbe56e057f20f883e', '13600136001', '管理员', 3),
('zhao_ops',  'e10adc3949ba59abbe56e057f20f883e', '13900139002', '赵运营', 1),
('sun_npc',   'e10adc3949ba59abbe56e057f20f883e', '13700137003', '孙NPC',  2),
('qian_tour', 'e10adc3949ba59abbe56e057f20f883e', '13800138004', '钱多多', 0);

-- =============================================
-- 4.2 剧本数据（10条）
-- =============================================
INSERT INTO Script (name, description, difficulty, duration, min_players, max_players, status) VALUES
('古墓迷踪',     '一场发生在千年古墓中的悬疑探险，玩家需要解开层层谜题找到真相',             3, 90,  4, 8,  1),
('江南烟雨',     '民国时期的江南小镇，一段尘封的往事等待被揭开',                             2, 60,  3, 6,  1),
('星际迷航',     '未来太空站上的神秘事件，高科技与推理的完美结合',                           4, 120, 5, 10, 0),
('血色书院',     '民国书院中发生的连环失踪案，每个角色都有不可告人的秘密',                   3, 90,  4, 8,  1),
('天空之城',     '漂浮在云端的失落文明，玩家需要解开古代机关的谜题唤醒城市',                 2, 75,  3, 6,  0),
('暗夜追凶',     '黑暗中的连环命案，侦探与凶手之间的智力博弈，每个人都是嫌疑人',             4, 120, 5, 10, 1),
('桃花源记',     '误入世外桃源的奇幻之旅，轻松愉快的解谜体验，适合新手入门',                 1, 45,  2, 4,  1),
('末日迷城',     '核战后的废墟城市中寻找幸存者，高难度生存推理，考验团队协作能力',           5, 150, 6, 12, 0),
('长安十二时辰', '盛唐时期的长安城，十二个时辰内阻止一场惊天阴谋，与时间赛跑',               3, 100, 4, 8,  1),
('梦境侦探',     '潜入他人梦境寻找线索，虚实交织的推理体验，AR梦境场景极具沉浸感',          2, 60,  3, 5,  0);

-- =============================================
-- 4.3 角色数据（12条：剧本1=4角色，剧本2=3角色，剧本4=3角色，剧本5=2角色）
-- =============================================
INSERT INTO Role (script_id, name, description, is_key_role, sort_order) VALUES
(1, '考古学家',   '拥有丰富的历史知识，擅长解读古文',                   1, 1),
(1, '探险家',     '身手矫健，擅长探索未知区域',                         0, 2),
(1, '文物鉴定师', '能鉴别文物的真伪与价值',                             0, 3),
(1, '记者',       '敏锐的洞察力，善于发现细节',                         0, 4),
(2, '茶馆老板娘', '知晓小镇上所有人的秘密',                             1, 1),
(2, '教书先生',   '温文尔雅，暗藏玄机',                                 0, 2),
(2, '巡警',       '维护小镇治安，掌握关键线索',                         0, 3),
(4, '校长',       '表面慈祥的校长，似乎隐藏着书院的秘密',               1, 1),
(4, '美术老师',   '才华横溢的艺术家，对书院的历史了如指掌',             0, 2),
(4, '校工',       '在书院工作多年，知道很多不为人知的通道和密道',       0, 3),
(5, '天空学者',   '研究失落文明的专家，能解读古代符文',                 1, 1),
(5, '飞行工程师', '掌握飞行技术，负责维护通往天空之城的飞行器',         0, 2);

-- =============================================
-- 4.4 线索数据（12条：剧本1=4条，剧本2=3条，剧本4=3条，剧本6=2条）
-- =============================================
INSERT INTO Clue (script_id, name, content, clue_type, trigger_type, sequence_num) VALUES
(1, '神秘地图',   '一张标注着奇怪符号的羊皮地图',                       1, 0, 1),
(1, '残缺日记',   '记载了考古队最后几天的经历，有几页被撕掉了',          0, 0, 2),
(1, '青铜器物',   '一个刻有铭文的青铜器，铭文似乎暗示着机关的位置',      1, 1, 3),
(1, '密室钥匙',   '在石像背后发现了一把古老的钥匙',                      2, 2, 4),
(2, '旧照片',     '一张泛黄的照片，背后写着一行小字',                     1, 0, 1),
(2, '匿名信',     '一封没有署名的信，提到了一桩旧事',                     0, 1, 2),
(2, '怀表',       '在茶馆角落发现的一块怀表，里面藏着一张微型照片',      3, 2, 3),
(4, '残缺成绩单', '一份被撕碎又拼回来的成绩单，有些名字被涂黑了',         1, 0, 1),
(4, '密室钥匙2',  '校长室暗格中找到的铜钥匙，上面刻着"禁地"二字',        2, 1, 2),
(4, '旧校刊',     '二十年前的书院校刊，头版报道了一起离奇的失踪事件',     0, 2, 3),
(6, '犯罪现场照片','第一起命案的现场照片，地毯上有一个奇怪的符号',        1, 0, 1),
(6, '验尸报告',   '法医的初步验尸报告，死因疑点重重',                     0, 1, 2);

-- =============================================
-- 4.5 打卡点数据（10条）
-- =============================================
INSERT INTO CheckPoint (name, latitude, longitude, is_required, description) VALUES
('古墓入口',  30.1234567, 120.9876543, 1, '古墓的入口处，有一扇巨大的石门'),
('主墓室',    30.1234678, 120.9876654, 1, '墓室中央摆放着一具石棺'),
('耳室',      30.1234789, 120.9876765, 0, '墓室两侧的小房间，堆放着陪葬品'),
('暗道',      30.1234890, 120.9876876, 0, '一条隐秘的通道，通向未知的地方'),
('小镇广场',  31.2345678, 121.8765432, 1, '江南小镇的中心广场'),
('老茶馆',    31.2345789, 121.8765543, 1, '镇上有名的老茶馆，老板娘在这里经营多年'),
('学堂',      31.2345890, 121.8765654, 0, '小镇唯一的学堂，教书先生在此授课'),
('书院大门',  32.3456789, 122.7654321, 1, '血色书院的正门，门上的匾额有些褪色'),
('图书馆',    32.3456890, 122.7654432, 1, '书院的图书馆，据说有人在深夜听到翻书声'),
('后山禁地',  32.3456901, 122.7654543, 0, '书院后山被铁丝网围住的区域，立着"危险勿入"的牌子');

-- =============================================
-- 4.6 场次数据（11条）
-- =============================================
INSERT INTO `Session` (script_id, start_time, end_time, max_players, current_players, price, status) VALUES
(1,  '2026-06-10 09:00:00', '2026-06-10 11:00:00', 8, 3, 128.00, 0),
(1,  '2026-06-10 14:00:00', '2026-06-10 16:00:00', 8, 5, 128.00, 0),
(1,  '2026-06-11 09:00:00', '2026-06-11 11:00:00', 8, 0, 118.00, 0),
(2,  '2026-06-10 10:00:00', '2026-06-10 11:30:00', 6, 4, 88.00,  0),
(2,  '2026-06-11 14:00:00', '2026-06-11 15:30:00', 6, 2, 88.00,  0),
(4,  '2026-06-12 09:00:00', '2026-06-12 11:00:00', 8, 6, 108.00, 0),
(4,  '2026-06-12 14:00:00', '2026-06-12 16:00:00', 8, 0, 108.00, 0),
(6,  '2026-06-13 10:00:00', '2026-06-13 12:30:00', 10, 7, 158.00, 0),
(6,  '2026-06-13 15:00:00', '2026-06-13 17:30:00', 10, 4, 158.00, 0),
(7,  '2026-06-14 09:00:00', '2026-06-14 10:30:00', 4, 2, 58.00,  0),
(9,  '2026-06-14 13:00:00', '2026-06-14 15:00:00', 8, 0, 138.00, 0);

-- =============================================
-- 4.7 订单数据（10条）
-- =============================================
INSERT INTO `Order` (user_id, session_id, role_id, amount, payment_status, payment_time) VALUES
(1,  1,  1,  128.00, 1, '2026-06-08 10:30:00'),
(2,  1,  2,  128.00, 1, '2026-06-08 11:00:00'),
(3,  1,  3,  128.00, 0, NULL),
(1,  2,  1,  128.00, 1, '2026-06-09 09:00:00'),
(2,  2,  2,  128.00, 1, '2026-06-09 09:15:00'),
(3,  2,  3,  128.00, 1, '2026-06-09 09:30:00'),
(2,  4,  5,  88.00,  1, '2026-06-09 14:00:00'),
(3,  4,  6,  88.00,  1, '2026-06-09 14:30:00'),
(10, 6,  8,  108.00, 1, '2026-06-11 10:00:00'),
(10, 8,  11, 158.00, 1, '2026-06-12 15:00:00');

-- =============================================
-- 4.8 NPC排班数据（10条）
-- =============================================
INSERT INTO NpcSchedule (npc_id, session_id, duty_role, schedule_date, status) VALUES
(5, 1,  'DM',         '2026-06-10', 0),
(5, 4,  'DM',         '2026-06-10', 0),
(6, 1,  '守墓老人',   '2026-06-10', 0),
(6, 2,  'DM',         '2026-06-10', 0),
(5, 6,  'DM',         '2026-06-12', 0),
(6, 6,  '书院管家',   '2026-06-12', 0),
(9, 6,  '神秘学生',   '2026-06-12', 0),
(9, 8,  'DM',         '2026-06-13', 0),
(5, 10, 'DM',         '2026-06-14', 0),
(9, 11, '唐朝密探',   '2026-06-14', 0);

-- =============================================
-- 4.9 游玩进度数据（10条）
-- =============================================
INSERT INTO PlayerProgress (user_id, session_id, current_clue_seq, status, start_time) VALUES
(1,  1,  0, 0, '2026-06-10 09:00:00'),
(2,  1,  1, 0, '2026-06-10 09:00:00'),
(1,  2,  0, 0, '2026-06-10 14:00:00'),
(2,  4,  1, 0, '2026-06-10 10:00:00'),
(3,  1,  2, 0, '2026-06-10 09:00:00'),
(10, 6,  0, 0, '2026-06-12 09:00:00'),
(10, 8,  1, 0, '2026-06-13 10:00:00'),
(2,  6,  2, 0, '2026-06-12 09:00:00'),
(3,  6,  1, 0, '2026-06-12 09:00:00'),
(2,  8,  0, 0, '2026-06-13 10:00:00');

-- =============================================
-- 4.10 评价数据（10条）
-- =============================================
INSERT INTO Review (user_id, session_id, script_id, rating, content) VALUES
(1,  1,  1, 5, '非常精彩的剧本！古墓场景的AR效果特别震撼，线索设计也很巧妙。'),
(2,  4,  2, 4, '江南烟雨的剧情很感人，AR茶馆场景做得很有氛围感，就是难度偏低了点。'),
(3,  1,  1, 5, '考古学家的角色代入感极强，解密过程环环相扣，强烈推荐！'),
(10, 6,  4, 4, '血色书院的气氛营造得很好，AR场景里的旧校舍还原度很高。'),
(10, 8,  6, 5, '暗夜追凶的逻辑非常严密，凶手隐藏得很深，玩完一身冷汗！'),
(2,  6,  4, 3, '书院的谜题有些地方逻辑不太通顺，不过场景氛围还是不错的。'),
(1,  2,  1, 4, '第二次玩古墓迷踪了，选了记者视角，发现了很多第一次没注意到的细节。'),
(2,  8,  6, 5, '暗夜追凶的侦探角色体验极佳，AR现场勘查功能很实用。'),
(3,  6,  4, 4, '血色书院的故事背景很有深度，建议多注意校长的台词。'),
(1,  8,  6, 4, '剧本难度确实高，我们队差点超时，但通关后的成就感满满。');

CREATE VIEW View_SessionOverview AS
SELECT
    se.session_id,
    s.name AS script_name,
    se.start_time,
    se.status,
    se.current_players,
    se.max_players,
    se.price,
    (se.max_players - se.current_players) AS available_spots,
    COUNT(o.order_id) AS paid_orders
FROM `Session` se
JOIN Script s ON se.script_id = s.script_id
LEFT JOIN `Order` o ON se.session_id = o.session_id AND o.payment_status = 1
GROUP BY se.session_id;

CREATE VIEW View_ScriptRating AS
SELECT
    s.script_id,
    s.name AS script_name,
    s.difficulty,
    COUNT(rv.review_id) AS review_count,
    ROUND(AVG(rv.rating), 2) AS avg_rating,
    MAX(rv.rating) AS max_rating,
    MIN(rv.rating) AS min_rating
FROM Script s
LEFT JOIN Review rv ON s.script_id = rv.script_id
GROUP BY s.script_id, s.name, s.difficulty;

DELIMITER //

CREATE TRIGGER trg_order_payment_update_session
AFTER UPDATE ON `Order`
FOR EACH ROW
BEGIN
    -- 场景1：订单从未支付(0)变为已支付(1) → 场次报名人数+1
    IF OLD.payment_status = 0 AND NEW.payment_status = 1 THEN
        UPDATE `Session`
        SET current_players = current_players + 1
        WHERE session_id = NEW.session_id;
    END IF;

    -- 场景2：订单从已支付(1)变为已退款(2) → 场次报名人数-1
    IF OLD.payment_status = 1 AND NEW.payment_status = 2 THEN
        UPDATE `Session`
        SET current_players = current_players - 1
        WHERE session_id = NEW.session_id;
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER trg_npcschedule_conflict_check
BEFORE INSERT ON NpcSchedule
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;

    -- 检查同一NPC在同一日期是否已有排班（通过场次时间判断重叠）
    SELECT COUNT(*) INTO conflict_count
    FROM NpcSchedule ns
    JOIN `Session` s ON ns.session_id = s.session_id
    JOIN `Session` s_new ON s_new.session_id = NEW.session_id
    WHERE ns.npc_id = NEW.npc_id
      AND ns.schedule_id != NEW.schedule_id
      AND ns.schedule_date = NEW.schedule_date
      AND (
          (s.start_time <= s_new.start_time AND s.end_time > s_new.start_time)
          OR
          (s_new.start_time <= s.start_time AND s_new.end_time > s.start_time)
      );

    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '该NPC在此时间段已有排班，存在时间冲突';
    END IF;
END //

DELIMITER ;

CREATE ROLE role_tourist, role_npc, role_operator, role_admin;

-- 查询权限：可浏览剧本、场次、角色信息
GRANT SELECT ON Script TO role_tourist;
GRANT SELECT ON Role TO role_tourist;
GRANT SELECT ON `Session` TO role_tourist;
GRANT SELECT ON CheckPoint TO role_tourist;

-- 订单操作：可查看自己的订单、提交新订单
GRANT SELECT, INSERT ON `Order` TO role_tourist;

-- 进度操作：查看自己的游玩进度
GRANT SELECT ON PlayerProgress TO role_tourist;

-- 评价操作：提交和查看评价
GRANT SELECT, INSERT ON Review TO role_tourist;

-- 个人信息：查看和修改个人资料
GRANT SELECT, UPDATE (nickname, phone, email, avatar_url) ON User TO role_tourist;

-- 查询权限：查看剧本和角色信息
GRANT SELECT ON Script TO role_npc;
GRANT SELECT ON Role TO role_npc;
GRANT SELECT ON Clue TO role_npc;

-- 场次信息：查看被分配的场次
GRANT SELECT ON `Session` TO role_npc;

-- 排班信息：查看自己的排班
GRANT SELECT ON NpcSchedule TO role_npc;

-- 游客进度：查看并更新游客游玩状态
GRANT SELECT, UPDATE (status, current_clue_seq, last_active_time) ON PlayerProgress TO role_npc;

-- 个人信息：查看和修改个人资料
GRANT SELECT, UPDATE (nickname, phone, avatar_url) ON User TO role_npc;

-- 剧本管理：完整CRUD
GRANT SELECT, INSERT, UPDATE, DELETE ON Script TO role_operator;
GRANT SELECT, INSERT, UPDATE, DELETE ON Role TO role_operator;
GRANT SELECT, INSERT, UPDATE, DELETE ON Clue TO role_operator;

-- 打卡点管理
GRANT SELECT, INSERT, UPDATE, DELETE ON CheckPoint TO role_operator;

-- 场次管理
GRANT SELECT, INSERT, UPDATE, DELETE ON `Session` TO role_operator;

-- 订单查看（只读+退款操作）
GRANT SELECT, UPDATE (payment_status) ON `Order` TO role_operator;

-- NPC排班管理
GRANT SELECT, INSERT, UPDATE, DELETE ON NpcSchedule TO role_operator;

-- 进度查看
GRANT SELECT ON PlayerProgress TO role_operator;

-- 评价管理（查看和删除违规评价）
GRANT SELECT, DELETE ON Review TO role_operator;

-- 用户查看
GRANT SELECT ON User TO role_operator;

-- 管理员拥有所有表的全部权限
GRANT ALL PRIVILEGES ON immersive_script_db.* TO role_admin;

-- 额外：可管理其他角色和用户
GRANT CREATE ROLE, DROP ROLE ON *.* TO role_admin;

-- 示例：将角色分配给具体数据库用户
-- （实际部署时，每个业务用户对应一个数据库用户）
CREATE USER 'zhangsan'@'localhost' IDENTIFIED BY 'password123';
GRANT role_tourist TO 'zhangsan'@'localhost';

CREATE USER 'npc_zhou'@'localhost' IDENTIFIED BY 'password123';
GRANT role_npc TO 'npc_zhou'@'localhost';

CREATE USER 'operator_li'@'localhost' IDENTIFIED BY 'password123';
GRANT role_operator TO 'operator_li'@'localhost';

CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'password123';
GRANT role_admin TO 'admin_user'@'localhost';

-- 激活角色（用户登录后）
SET DEFAULT ROLE ALL TO 'zhangsan'@'localhost';
SET DEFAULT ROLE ALL TO 'npc_zhou'@'localhost';
SET DEFAULT ROLE ALL TO 'operator_li'@'localhost';
SET DEFAULT ROLE ALL TO 'admin_user'@'localhost';

DELIMITER //

CREATE PROCEDURE proc_session_report(
    IN p_script_id INT,          -- 剧本ID（可选，NULL表示全部）
    IN p_start_date DATE,        -- 起始日期
    IN p_end_date DATE           -- 结束日期
)
BEGIN
    -- 临时变量：总订单数、总收入
    DECLARE v_total_orders INT DEFAULT 0;
    DECLARE v_total_revenue DECIMAL(12, 2) DEFAULT 0;

    -- 1. 统计总订单数和总收入
    SELECT COUNT(o.order_id), COALESCE(SUM(o.amount), 0)
    INTO v_total_orders, v_total_revenue
    FROM `Session` se
    LEFT JOIN `Order` o ON se.session_id = o.session_id AND o.payment_status = 1
    WHERE (p_script_id IS NULL OR se.script_id = p_script_id)
      AND DATE(se.start_time) BETWEEN p_start_date AND p_end_date;

    -- 2. 输出汇总信息
    SELECT
        p_script_id AS query_script_id,
        p_start_date AS date_from,
        p_end_date AS date_to,
        v_total_orders AS total_paid_orders,
        v_total_revenue AS total_revenue;

    -- 3. 输出逐场次明细
    SELECT
        s.name AS script_name,
        se.session_id,
        se.start_time,
        se.status,
        CONCAT(se.current_players, '/', se.max_players) AS occupancy,
        ROUND(se.current_players / se.max_players * 100, 1) AS occupancy_rate,
        se.price,
        COUNT(o.order_id) AS paid_order_count,
        COALESCE(SUM(o.amount), 0) AS session_revenue
    FROM `Session` se
    JOIN Script s ON se.script_id = s.script_id
    LEFT JOIN `Order` o ON se.session_id = o.session_id AND o.payment_status = 1
    WHERE (p_script_id IS NULL OR se.script_id = p_script_id)
      AND DATE(se.start_time) BETWEEN p_start_date AND p_end_date
    GROUP BY se.session_id
    ORDER BY se.start_time;

END //

DELIMITER ;

CREATE INDEX idx_order_user_time ON `Order`(user_id, order_time);

CREATE INDEX idx_session_start_time ON `Session`(start_time);

CREATE INDEX idx_clue_script_sequence ON Clue(script_id, sequence_num);

-- 前置：查看场次1当前报名人数
SELECT session_id, current_players, max_players FROM `Session` WHERE session_id = 1;

-- 模拟：将用户3（wangwu）的订单从未支付改为已支付
UPDATE `Order` SET payment_status = 1, payment_time = NOW()
WHERE order_id = 3;

-- 验证：场次1的current_players应+1
SELECT session_id, current_players, max_players FROM `Session` WHERE session_id = 1;

-- 前置：查看NPC周某（npc_id=5）和场次信息
SELECT npc_id, session_id, duty_role, schedule_date FROM NpcSchedule WHERE npc_id = 5;
SELECT session_id, start_time, end_time FROM `Session`;

-- 测试1：插入不冲突的排班（预期成功）
INSERT INTO NpcSchedule (npc_id, session_id, duty_role, schedule_date, status)
VALUES (5, 5, 'DM', '2026-06-11', 0);
-- 期望：插入成功

-- 测试2：插入冲突排班（预期失败 - 场次1与npc_id=5已有排班冲突）
-- npc_id=5已在场次1(2026-06-10 09:00-11:00)排班为DM
-- 尝试在场次1的相同时间段再排一次
INSERT INTO NpcSchedule (npc_id, session_id, duty_role, schedule_date, status)
VALUES (5, 1, '守墓老人', '2026-06-10', 0);
-- 期望：触发器阻止，返回错误 "该NPC在此时间段已有排班，存在时间冲突"

SELECT
    se.session_id,
    se.start_time,
    s.name AS script_name,
    u.nickname AS player_name,
    r.name AS role_name,
    o.amount,
    CASE o.payment_status
        WHEN 0 THEN '未支付'
        WHEN 1 THEN '已支付'
        WHEN 2 THEN '已退款'
    END AS payment_status
FROM `Session` se
JOIN Script s ON se.script_id = s.script_id
JOIN `Order` o ON se.session_id = o.session_id
JOIN User u ON o.user_id = u.user_id
LEFT JOIN Role r ON o.role_id = r.role_id
WHERE se.session_id = 1
ORDER BY o.order_time;

SELECT u.nickname AS npc_name, u.phone AS npc_phone,
       ns.duty_role, ns.schedule_date, ns.status
FROM User u
JOIN NpcSchedule ns ON u.user_id = ns.npc_id
WHERE u.role_type = 2
  AND EXISTS (
    SELECT 1 FROM `Session` se
    WHERE se.session_id = ns.session_id
      AND se.status = 2
  )
  AND ns.status IN (0, 3)
ORDER BY ns.schedule_date;

SELECT u.nickname, u.phone, u.create_time,
       (SELECT COUNT(*) FROM `Order` o
        WHERE o.user_id = u.user_id) AS total_orders,
       (SELECT COALESCE(SUM(o.amount), 0) FROM `Order` o
        WHERE o.user_id = u.user_id
          AND o.payment_status = 1) AS total_spent
FROM User u
WHERE (SELECT COUNT(*) FROM `Order` o WHERE o.user_id = u.user_id) >= 2
ORDER BY total_orders DESC, total_spent DESC;

SELECT s.name AS script_name, s.difficulty,
       COUNT(DISTINCT se.session_id) AS session_count,
       COUNT(DISTINCT o.order_id) AS order_count,
       COALESCE(SUM(o.amount), 0) AS total_revenue,
       ROUND(AVG(rv.rating), 2) AS avg_rating
FROM Script s
LEFT JOIN `Session` se ON s.script_id = se.script_id
LEFT JOIN `Order` o
    ON se.session_id = o.session_id AND o.payment_status = 1
LEFT JOIN Review rv ON s.script_id = rv.script_id
GROUP BY s.script_id, s.name, s.difficulty
HAVING total_revenue < 500
ORDER BY total_revenue DESC;

SELECT s.script_id, s.name, s.difficulty, s.duration,
       s.max_players, s.cover_url,
       COALESCE(rs.review_count, 0) AS review_count,
       COALESCE(rs.avg_rating, 0) AS avg_rating
FROM Script s
LEFT JOIN View_ScriptRating rs ON s.script_id = rs.script_id
WHERE s.status = 1
ORDER BY avg_rating DESC, review_count DESC
LIMIT 3 OFFSET 0;

-- 存储过程验证SQL：
-- 测试1：查询剧本1（古墓迷踪）在2026-06-01到2026-06-30期间的运营数据
CALL proc_session_report(1, '2026-06-01', '2026-06-30');

-- 测试2：查询所有剧本在2026年6月的运营数据（script_id=NULL）
CALL proc_session_report(NULL, '2026-06-01', '2026-06-30');

-- 测试3：查询无数据的日期范围
CALL proc_session_report(1, '2026-07-01', '2026-07-31');

