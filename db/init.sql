-- =====================================================================
--  实验室设备预约与智能报修平台 —— 数据库初始化脚本
--  数据库：MySQL 8.0+    字符集：utf8mb4
--  用法：mysql -u root -p < db/init.sql
--  说明：脚本会重建全部业务表并写入演示用种子数据（账号、设备、预约、
--        报修、知识文档元数据）。演示数据的时间基于 NOW() 计算，
--        因此任何时间执行都能得到"正在进行/即将开始"的样例。
--        所有姓名、联系方式均为虚构，仅用于课程演示。
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `labcare`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `labcare`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `agent_run`;
DROP TABLE IF EXISTS `pending_action`;
DROP TABLE IF EXISTS `chat_message`;
DROP TABLE IF EXISTS `chat_session`;
DROP TABLE IF EXISTS `knowledge_chunk`;
DROP TABLE IF EXISTS `knowledge_document`;
DROP TABLE IF EXISTS `operation_log`;
DROP TABLE IF EXISTS `repair_ticket`;
DROP TABLE IF EXISTS `reservation`;
DROP TABLE IF EXISTS `equipment`;
DROP TABLE IF EXISTS `app_user`;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. 用户（角色只有普通用户 USER 与管理员 ADMIN，管理员兼维修人员）
-- ---------------------------------------------------------------------
CREATE TABLE `app_user` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(50)     NOT NULL COMMENT '登录名',
  `password_hash` VARCHAR(100)    NOT NULL COMMENT 'BCrypt 摘要，禁止明文',
  `display_name`  VARCHAR(50)     NOT NULL COMMENT '显示名',
  `role`          VARCHAR(20)     NOT NULL DEFAULT 'USER' COMMENT 'USER / ADMIN',
  `status`        TINYINT         NOT NULL DEFAULT 1 COMMENT '1 启用 / 0 停用',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`)
) ENGINE = InnoDB COMMENT = '系统用户';

-- ---------------------------------------------------------------------
-- 2. 设备台账
-- ---------------------------------------------------------------------
CREATE TABLE `equipment` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code`        VARCHAR(40)     NOT NULL COMMENT '设备编号，业务唯一',
  `name`        VARCHAR(100)    NOT NULL,
  `category`    VARCHAR(50)     NOT NULL COMMENT '设备类别',
  `laboratory`  VARCHAR(100)    NOT NULL COMMENT '所属实验室',
  `location`    VARCHAR(100)    DEFAULT NULL COMMENT '具体位置',
  `status`      VARCHAR(20)     NOT NULL DEFAULT 'AVAILABLE' COMMENT 'AVAILABLE 可用 / MAINTENANCE 维修中 / DISABLED 停用',
  `description` VARCHAR(500)    DEFAULT NULL COMMENT '设备简介',
  `usage_note`  VARCHAR(500)    DEFAULT NULL COMMENT '使用说明与注意事项',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_equipment_code` (`code`),
  KEY `idx_equipment_filter` (`category`, `laboratory`, `status`)
) ENGINE = InnoDB COMMENT = '实验室设备台账';

-- ---------------------------------------------------------------------
-- 3. 预约单
--    状态流转：PENDING -> APPROVED / REJECTED；PENDING -> CANCELLED（本人取消）
--              APPROVED -> COMPLETED（管理员在结束后标记）；APPROVED -> CANCELLED（管理员撤销，可选）
-- ---------------------------------------------------------------------
CREATE TABLE `reservation` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code`           VARCHAR(32)     NOT NULL COMMENT '预约编号，业务唯一',
  `equipment_id`   BIGINT UNSIGNED NOT NULL,
  `user_id`        BIGINT UNSIGNED NOT NULL COMMENT '申请人',
  `start_time`     DATETIME        NOT NULL,
  `end_time`       DATETIME        NOT NULL,
  `purpose`        VARCHAR(200)    DEFAULT NULL COMMENT '用途',
  `status`         VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                   COMMENT 'PENDING 待审核 / APPROVED 已通过 / REJECTED 已驳回 / CANCELLED 已取消 / COMPLETED 已完成',
  `reviewer_id`    BIGINT UNSIGNED DEFAULT NULL,
  `review_comment` VARCHAR(200)    DEFAULT NULL,
  `reviewed_at`    DATETIME        DEFAULT NULL,
  `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_reservation_code` (`code`),
  KEY `idx_reservation_equipment_time` (`equipment_id`, `start_time`, `end_time`),
  KEY `idx_reservation_user` (`user_id`),
  KEY `idx_reservation_status` (`status`),
  CONSTRAINT `fk_reservation_equipment` FOREIGN KEY (`equipment_id`) REFERENCES `equipment` (`id`),
  CONSTRAINT `fk_reservation_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`id`),
  CONSTRAINT `fk_reservation_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `app_user` (`id`)
) ENGINE = InnoDB COMMENT = '设备预约申请';

-- ---------------------------------------------------------------------
-- 4. 报修工单
--    状态流转：PENDING -> PROCESSING -> COMPLETED；PENDING/PROCESSING -> CLOSED
-- ---------------------------------------------------------------------
CREATE TABLE `repair_ticket` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code`         VARCHAR(32)     NOT NULL COMMENT '工单编号，业务唯一',
  `equipment_id` BIGINT UNSIGNED NOT NULL,
  `user_id`      BIGINT UNSIGNED NOT NULL COMMENT '提交人',
  `contact`      VARCHAR(50)     DEFAULT NULL COMMENT '联系方式（演示用虚构信息）',
  `description`  VARCHAR(1000)   NOT NULL COMMENT '故障描述',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                 COMMENT 'PENDING 待受理 / PROCESSING 处理中 / COMPLETED 已完成 / CLOSED 已关闭',
  `handler_id`   BIGINT UNSIGNED DEFAULT NULL COMMENT '受理人',
  `resolution`   VARCHAR(1000)   DEFAULT NULL COMMENT '处理结果',
  `accepted_at`  DATETIME        DEFAULT NULL,
  `completed_at` DATETIME        DEFAULT NULL,
  `source`       VARCHAR(20)     NOT NULL DEFAULT 'MANUAL' COMMENT 'MANUAL 手动提交 / AGENT 智能助手创建',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_repair_code` (`code`),
  KEY `idx_repair_user` (`user_id`),
  KEY `idx_repair_status` (`status`),
  CONSTRAINT `fk_repair_equipment` FOREIGN KEY (`equipment_id`) REFERENCES `equipment` (`id`),
  CONSTRAINT `fk_repair_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`id`),
  CONSTRAINT `fk_repair_handler` FOREIGN KEY (`handler_id`) REFERENCES `app_user` (`id`)
) ENGINE = InnoDB COMMENT = '故障报修工单';

-- ---------------------------------------------------------------------
-- 5. 操作日志（审核、状态变更、Agent 建单等关键动作）
-- ---------------------------------------------------------------------
CREATE TABLE `operation_log` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `operator_id`   BIGINT UNSIGNED DEFAULT NULL,
  `operator_name` VARCHAR(50)     DEFAULT NULL COMMENT '冗余保存，便于日志追溯',
  `target_type`   VARCHAR(30)     NOT NULL COMMENT 'EQUIPMENT / RESERVATION / REPAIR / KNOWLEDGE / AGENT',
  `target_id`     VARCHAR(64)     DEFAULT NULL,
  `action`        VARCHAR(40)     NOT NULL,
  `summary`       VARCHAR(500)    DEFAULT NULL,
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_log_target` (`target_type`, `target_id`)
) ENGINE = InnoDB COMMENT = '关键操作记录';

-- ---------------------------------------------------------------------
-- 6. 知识库文档与分片（原文分片存 MySQL，向量存 Chroma）
-- ---------------------------------------------------------------------
CREATE TABLE `knowledge_document` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title`         VARCHAR(200)    NOT NULL,
  `source_name`   VARCHAR(200)    NOT NULL COMMENT '原始文件名',
  `file_type`     VARCHAR(20)     NOT NULL COMMENT 'txt / md / pdf / docx',
  `file_size`     BIGINT          NOT NULL DEFAULT 0,
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                  COMMENT 'PENDING 待处理 / INDEXING 索引中 / READY 可检索 / FAILED 失败',
  `chunk_count`   INT             NOT NULL DEFAULT 0,
  `error_message` VARCHAR(500)    DEFAULT NULL,
  `uploaded_by`   BIGINT UNSIGNED DEFAULT NULL,
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_kdoc_status` (`status`)
) ENGINE = InnoDB COMMENT = '知识库文档';

CREATE TABLE `knowledge_chunk` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `document_id` BIGINT UNSIGNED NOT NULL,
  `chunk_index` INT             NOT NULL,
  `content`     TEXT            NOT NULL,
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_kchunk_doc` (`document_id`, `chunk_index`),
  CONSTRAINT `fk_kchunk_doc` FOREIGN KEY (`document_id`) REFERENCES `knowledge_document` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = '知识文档分片';

-- ---------------------------------------------------------------------
-- 7. AI 会话、消息、Agent 执行轨迹与待确认动作
-- ---------------------------------------------------------------------
CREATE TABLE `chat_session` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `title`      VARCHAR(100)    NOT NULL DEFAULT '新会话',
  `mode`       VARCHAR(20)     NOT NULL DEFAULT 'RAG' COMMENT 'RAG 知识问答 / AGENT 智能助手',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_chat_user` (`user_id`, `mode`)
) ENGINE = InnoDB COMMENT = 'AI 会话';

CREATE TABLE `chat_message` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id`    BIGINT UNSIGNED NOT NULL,
  `role`          VARCHAR(20)     NOT NULL COMMENT 'user / assistant',
  `content`       TEXT            NOT NULL,
  `citations`     JSON            DEFAULT NULL COMMENT '引用来源数组',
  `degraded`      TINYINT         NOT NULL DEFAULT 0 COMMENT '1 表示降级模式生成',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_msg_session` (`session_id`, `id`),
  CONSTRAINT `fk_msg_session` FOREIGN KEY (`session_id`) REFERENCES `chat_session` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = 'AI 会话消息';

CREATE TABLE `agent_run` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id`     BIGINT UNSIGNED DEFAULT NULL,
  `user_id`        BIGINT UNSIGNED DEFAULT NULL,
  `step_no`        INT             NOT NULL DEFAULT 1,
  `tool_name`      VARCHAR(60)     DEFAULT NULL,
  `input_summary`  VARCHAR(500)    DEFAULT NULL,
  `output_summary` VARCHAR(500)    DEFAULT NULL,
  `success`        TINYINT         NOT NULL DEFAULT 1,
  `error_message`  VARCHAR(500)    DEFAULT NULL,
  `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_run_session` (`session_id`, `id`)
) ENGINE = InnoDB COMMENT = 'Agent 工具调用轨迹';

CREATE TABLE `pending_action` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `token`       VARCHAR(64)     NOT NULL COMMENT '确认令牌，一次性',
  `user_id`     BIGINT UNSIGNED NOT NULL,
  `session_id`  BIGINT UNSIGNED DEFAULT NULL,
  `action_type` VARCHAR(40)     NOT NULL COMMENT 'CREATE_REPAIR 等',
  `payload`     JSON            NOT NULL COMMENT '待提交内容',
  `preview`     VARCHAR(1000)   DEFAULT NULL COMMENT '面向用户的确认文案',
  `status`      VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING / CONFIRMED / CANCELLED / EXPIRED',
  `result_ref`  VARCHAR(64)     DEFAULT NULL COMMENT '确认后产生的业务编号',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at`  DATETIME        NOT NULL COMMENT '过期时间，默认 10 分钟',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pending_token` (`token`),
  KEY `idx_pending_user` (`user_id`, `status`)
) ENGINE = InnoDB COMMENT = 'Agent 写操作待确认动作';

-- =====================================================================
--  种子数据（全部为虚构演示数据）
-- =====================================================================

-- 演示账号：student01 / Student@123    student02 / Student@123    admin / Admin@123
INSERT INTO `app_user` (`id`, `username`, `password_hash`, `display_name`, `role`, `status`) VALUES
(1, 'student01', '$2b$10$fxAa.nEQZ4pB8VNbH/YYWOt/JO2jHTmI8SjOit9zf8XRnccTcThlC', '张同学', 'USER',  1),
(2, 'student02', '$2b$10$fxAa.nEQZ4pB8VNbH/YYWOt/JO2jHTmI8SjOit9zf8XRnccTcThlC', '李同学', 'USER',  1),
(3, 'admin',     '$2b$10$dGMV6SX0nN01se4JYJpoGey8eoEwWa1SQz9AxTCn5v62ZtQE1lPI2', '王老师', 'ADMIN', 1);

INSERT INTO `equipment` (`id`, `code`, `name`, `category`, `laboratory`, `location`, `status`, `description`, `usage_note`) VALUES
(1, 'EQ-001', '高速冷冻离心机', '离心设备',   '生物实验室 A-101', 'A-101 台面 1 号位', 'AVAILABLE',
 '最高转速 15000 rpm，支持 4℃ 冷冻，用于细胞与核酸样品分离。', '使用前确认转子无裂纹；配平误差不超过 0.1 g；运行中禁止开盖。'),
(2, 'EQ-002', '台式扫描电子显微镜', '成像设备', '材料分析实验室 B-203', 'B-203 主实验区', 'MAINTENANCE',
 '用于金属与复合材料表面形貌观察，放大倍数 10~300000 倍。', '样品需干燥导电；进样前完成喷金处理；由培训合格人员操作。'),
(3, 'EQ-003', '紫外可见分光光度计', '分析仪器', '化学分析实验室 A-305', 'A-305 仪器台 3 号位', 'AVAILABLE',
 '波长范围 190~1100 nm，用于溶液吸光度测定与浓度定量分析。', '开机预热 20 分钟；比色皿光面朝光路；强腐蚀样品需稀释后测定。'),
(4, 'EQ-004', '恒温培养箱', '培养设备', '生物实验室 A-102', 'A-102 培养区', 'AVAILABLE',
 '控温范围 5~60℃，用于微生物与细胞培养。', '箱内禁止放置易燃易爆物品；每日记录温度；开门时间尽量短。'),
(5, 'EQ-005', '高效液相色谱仪', '分析仪器', '化学分析实验室 A-306', 'A-306 色谱室', 'AVAILABLE',
 '用于有机物分离与定量分析，配置二元梯度泵与紫外检测器。', '流动相使用前需 0.45 μm 滤膜过滤并脱气；进样前冲洗色谱柱 30 分钟。'),
(6, 'EQ-006', '光固化 3D 打印机', '制造设备', '工程训练中心 C-01', 'C-01 打印区', 'AVAILABLE',
 '成型尺寸 192×120×245 mm，用于快速原型制作。', '树脂需避光保存；取件必须佩戴手套；打印完成后清洗并二次固化。'),
(7, 'EQ-007', '激光切割机', '制造设备', '工程训练中心 C-02', 'C-02 切割区', 'DISABLED',
 'CO2 激光切割机，切割幅面 600×400 mm。', '设备检修中，暂停预约；操作必须佩戴护目镜并开启排风。'),
(8, 'EQ-008', '电子万能试验机', '力学测试', '材料分析实验室 B-201', 'B-201 力学测试区', 'AVAILABLE',
 '最大试验力 100 kN，支持拉伸、压缩、弯曲试验。', '试样装夹需对中；超量程加载会损坏传感器；试验后及时卸载。'),
(9, 'EQ-009', '超纯水机', '辅助设备', '公共准备间 A-001', 'A-001 准备间', 'AVAILABLE',
 '产水电阻率 18.2 MΩ·cm，供实验室配液与清洗使用。', '取水前放水 30 秒；滤芯每 6 个月更换一次。'),
(10,'EQ-010', '生物安全柜', '防护设备', '生物实验室 A-103', 'A-103 洁净区', 'AVAILABLE',
 'Ⅱ级 A2 型生物安全柜，用于病原微生物操作防护。', '使用前紫外照射 30 分钟并开启风机 10 分钟；柜内物品不得遮挡前后格栅。');

-- 预约：一条已通过（明天），一条待审核（后天），一条已驳回，一条已完成
INSERT INTO `reservation` (`id`, `code`, `equipment_id`, `user_id`, `start_time`, `end_time`, `purpose`, `status`, `reviewer_id`, `review_comment`, `reviewed_at`, `created_at`) VALUES
(1, 'RS202611090001', 1, 1,
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 9 HOUR),
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 11 HOUR),
 '细胞样品离心分离', 'APPROVED', 3, '同意，请按操作规程使用。', NOW(), NOW()),
(2, 'RS202611090002', 3, 2,
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 2 DAY), INTERVAL 14 HOUR),
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 2 DAY), INTERVAL 16 HOUR),
 '水质吸光度测定', 'PENDING', NULL, NULL, NULL, NOW()),
(3, 'RS202611090003', 6, 2,
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 3 DAY), INTERVAL 10 HOUR),
 DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 3 DAY), INTERVAL 12 HOUR),
 '结构件原型打印', 'REJECTED', 3, '该时段设备已安排维护，请改约。', NOW(), NOW()),
(4, 'RS202611080001', 8, 1,
 DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 2 DAY), INTERVAL 9 HOUR),
 DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 2 DAY), INTERVAL 11 HOUR),
 '金属试样拉伸试验', 'COMPLETED', 3, '同意。', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY));

-- 报修：待受理、处理中、已完成、已关闭各一条
INSERT INTO `repair_ticket` (`id`, `code`, `equipment_id`, `user_id`, `contact`, `description`, `status`, `handler_id`, `resolution`, `accepted_at`, `completed_at`, `source`, `created_at`) VALUES
(1, 'RP202611090001', 2, 1, '13800000001',
 '电镜抽真空后真空度一直达不到设定值，屏幕提示 VACUUM TIMEOUT，已重启一次无效。', 'PENDING', NULL, NULL, NULL, NULL, 'MANUAL', NOW()),
(2, 'RP202611080001', 7, 2, '13800000002',
 '激光切割机切割面出现明显斜边，且切割功率不稳定，怀疑光路偏移。', 'PROCESSING', 3, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY), NULL, 'MANUAL', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(3, 'RP202611070001', 1, 2, '13800000002',
 '离心机运行时噪音明显增大，低速档位有轻微异响。', 'COMPLETED', 3,
 '已更换转子轴承并做动平衡校准，空载试运行 30 分钟正常。', DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY), 'MANUAL', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(4, 'RP202611060001', 9, 1, '13800000001',
 '超纯水机取水口出水电阻率只有 12 MΩ·cm，达不到 18.2。', 'CLOSED', 3,
 '经检查滤芯已到期，用户已自行更换，重复工单关闭。', DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY), 'MANUAL', DATE_SUB(NOW(), INTERVAL 7 DAY));

-- 知识库文档元数据（正文文件位于 data/知识库/，由 AI 服务解析入索引）
INSERT INTO `knowledge_document` (`id`, `title`, `source_name`, `file_type`, `file_size`, `status`, `chunk_count`, `uploaded_by`, `created_at`) VALUES
(1, '高速冷冻离心机使用手册', '离心机使用手册.md', 'md', 4200, 'READY', 0, 3, NOW()),
(2, '实验室安全操作规范', '实验室安全操作规范.txt', 'txt', 3800, 'READY', 0, 3, NOW()),
(3, '实验室设备常见故障处理指南', '常见故障处理指南.md', 'md', 5100, 'READY', 0, 3, NOW());

-- 操作日志样例
INSERT INTO `operation_log` (`operator_id`, `operator_name`, `target_type`, `target_id`, `action`, `summary`, `created_at`) VALUES
(3, '王老师', 'RESERVATION', 'RS202611090001', 'APPROVE', '审核通过，意见：同意，请按操作规程使用。', NOW()),
(3, '王老师', 'RESERVATION', 'RS202611090003', 'REJECT', '审核驳回，意见：该时段设备已安排维护，请改约。', NOW()),
(3, '王老师', 'REPAIR', 'RP202611080001', 'ACCEPT', '受理工单，状态更新为处理中。', DATE_SUB(NOW(), INTERVAL 1 DAY));
