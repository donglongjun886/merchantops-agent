-- MerchantOps Agent 数据层 schema（与 app/db/models.py 对应，实际建表以 SQLAlchemy create_all 为准）
-- 表关系：merchant 1:N task、merchant 1:N merchant_order；task 1:N task_progress
-- 字符集：utf8mb4；引擎：InnoDB

CREATE TABLE IF NOT EXISTS merchant (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    name        VARCHAR(128) NOT NULL COMMENT '商家名称',
    status      VARCHAR(16)  NOT NULL COMMENT '状态：ACTIVE/INACTIVE',
    created_at  DATETIME     NOT NULL DEFAULT (now()) COMMENT '创建时间',
    updated_at  DATETIME     NULL COMMENT '更新时间（手动维护）',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商家';

CREATE TABLE IF NOT EXISTS task (
    id           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    merchant_id  BIGINT       NOT NULL COMMENT '商家ID',
    name         VARCHAR(128) NOT NULL COMMENT '任务名称',
    metric_type  VARCHAR(16)  NOT NULL COMMENT '指标类型：GMV/ORDER_COUNT',
    target_value DECIMAL(14,2) NOT NULL COMMENT '目标值',
    start_time   DATETIME     NULL COMMENT '开始时间',
    end_time     DATETIME     NULL COMMENT '结束时间',
    status       VARCHAR(16)  NOT NULL COMMENT '状态：PENDING/IN_PROGRESS/COMPLETED/CANCELLED',
    created_at   DATETIME     NOT NULL DEFAULT (now()) COMMENT '创建时间',
    updated_at   DATETIME     NULL COMMENT '更新时间（手动维护）',
    PRIMARY KEY (id),
    KEY idx_task_merchant_id (merchant_id),
    CONSTRAINT fk_task_merchant FOREIGN KEY (merchant_id) REFERENCES merchant (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='经营任务';

CREATE TABLE IF NOT EXISTS task_progress (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    task_id       BIGINT       NOT NULL COMMENT '任务ID',
    current_value DECIMAL(14,2) NOT NULL COMMENT '当前值',
    progress      DECIMAL(5,2) NOT NULL COMMENT '完成百分比 0-100.00',
    status        VARCHAR(16)  NOT NULL COMMENT '状态：IN_PROGRESS/COMPLETED',
    completed_at  DATETIME     NULL COMMENT '完成时间（仅任务完成时有值）',
    created_at    DATETIME     NOT NULL DEFAULT (now()) COMMENT '创建时间',
    updated_at    DATETIME     NULL COMMENT '更新时间（手动维护）',
    PRIMARY KEY (id),
    KEY idx_task_progress_task_id (task_id),
    CONSTRAINT fk_task_progress_task FOREIGN KEY (task_id) REFERENCES task (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务进度';

CREATE TABLE IF NOT EXISTS merchant_order (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    order_id    VARCHAR(32)  NOT NULL COMMENT '业务订单号',
    merchant_id BIGINT       NOT NULL COMMENT '商家ID',
    amount      DECIMAL(14,2) NOT NULL COMMENT '订单金额',
    status      VARCHAR(16)  NOT NULL COMMENT '状态：PENDING/PAID/SHIPPED/COMPLETED/CANCELLED/REFUNDED/RISK_REVIEW',
    created_at  DATETIME     NOT NULL DEFAULT (now()) COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_merchant_order_order_id (order_id),
    KEY idx_merchant_order_merchant_id (merchant_id),
    CONSTRAINT fk_merchant_order_merchant FOREIGN KEY (merchant_id) REFERENCES merchant (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商家订单';

-- 说明：与 app/db/models.py 对应，实际建表以 SQLAlchemy create_all 为准
