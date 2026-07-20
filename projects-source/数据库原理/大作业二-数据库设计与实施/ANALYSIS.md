# 数据库设计与实施（沉浸式剧本选课）

## 项目概述

一个完整的沉浸式剧本杀业务数据库设计，涵盖用户管理、剧本管理、角色分配、线索链、打卡点、场次排期、订单支付、NPC 排班、游玩进度追踪和评价系统等 10 张核心表。同时包含一个独立的 SQL 实战操练部分，覆盖 20+ 道 SQL 查询练习。

## 架构设计

数据库以 Script（剧本）为业务核心，向外辐射关联 9 张表：Role 和 Clue 属于剧本的内容资产，CheckPoint 将虚拟线索映射到物理 GPS 位置，Session 和 Order 构成商家的运营和营收模块，NpcSchedule 管理人力排班，PlayerProgress 追踪玩家状态，Review 收集反馈。

外键约束确保数据完整性：Role/Clue 通过 script_id 级联删除，Order 通过 user_id 和 session_id 关联用户和场次，PlayerProgress 通过 uk_user_session 唯一约束保证同一用户在同一场次只能有一条进度记录。

视图与存储过程：View_SessionOverview 聚合场次概览（含余位和已支付订单数），View_ScriptRating 计算剧本评分统计。proc_session_report 存储过程接受剧本 ID 和日期范围参数，输出总订单数、总营收和逐场次明细。

## 技术亮点

触发器实现业务自动化：trg_order_payment_update_session 在订单支付状态变更时自动更新场次的 current_players 计数，无需应用层处理。trg_npcschedule_conflict_check 在插入排班前通过时间重叠检测防止 NPC 排班冲突，使用 SIGNAL SQLSTATE '45000' 抛出自定义错误。

RBAC 权限体系：使用 MySQL 的角色机制创建了 role_tourist/role_npc/role_operator/role_admin 四个数据库角色，每个角色精确控制可操作的表和列。tourist 只能查询和下单，npc 可更新游玩进度，operator 管理剧本内容，admin 拥有全部权限。

CHECK 约束与索引优化：通过 CHECK 约束确保角色类型、评分范围、难度等级的数据合法性。为常用查询字段建立 12 个索引，覆盖用户角色查询、订单状态查询、场次时间范围扫描等场景。

## 设计决策

命名规范遵循"表名+ID"的主键命名惯例，外键显式命名（fk_来源_目标）便于维护和错误定位。GPS 坐标使用 DECIMAL(10,7) 保证精度，price 使用 DECIMAL(10,2) 避免浮点误差。AR 相关内容预留 url 字段，为未来扩展留有余地。

## 关键代码解读

```sql
CREATE TRIGGER trg_npcschedule_conflict_check
BEFORE INSERT ON NpcSchedule
FOR EACH ROW
BEGIN
    SELECT COUNT(*) INTO conflict_count
    FROM NpcSchedule ns
    JOIN `Session` s ON ns.session_id = s.session_id
    WHERE ns.npc_id = NEW.npc_id
      AND (
          (s.start_time <= s_new.start_time AND s.end_time > s_new.start_time)
          OR (s_new.start_time <= s.start_time AND s_new.end_time > s.start_time)
      );
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '排班时间冲突';
    END IF;
END;
```

该触发器利用两段时间重叠的判断逻辑（时间段 A 的开始在 B 结束之前且 A 的结束在 B 开始之后），在插入排班前自动检测时间冲突。相比应用层检查，触发器从数据库层面保证排班数据的绝对一致性。
