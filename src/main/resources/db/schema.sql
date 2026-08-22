-- ============================================================
-- MerchantOps Agent 数据库结构
-- 业务表：merchant_order / product / task
-- Agent 表：agent_conversation（会话消息历史）/ agent_trace（每轮调用追踪，可观测性地基）
-- 幂等：IF NOT EXISTS，可重复执行
-- ============================================================

CREATE TABLE IF NOT EXISTS merchant_order (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    order_no    VARCHAR(32)  NOT NULL COMMENT '订单号',
    product_sku VARCHAR(32)  NOT NULL COMMENT '商品SKU',
    product_name VARCHAR(128) NOT NULL COMMENT '商品名称',
    quantity    INT          NOT NULL DEFAULT 1 COMMENT '数量',
    amount      DECIMAL(12,2) NOT NULL COMMENT '订单金额（元）',
    status      VARCHAR(16)  NOT NULL COMMENT '订单状态：PENDING/PAID/SHIPPED/COMPLETED/CANCELLED/REFUNDED',
    buyer_name  VARCHAR(64)  NOT NULL COMMENT '买家姓名',
    buyer_phone VARCHAR(20)  NOT NULL COMMENT '买家手机号（敏感字段）',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_status_created (status, created_at),
    KEY idx_sku (product_sku)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='订单表';

CREATE TABLE IF NOT EXISTS product (
    id          BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键',
    sku         VARCHAR(32)   NOT NULL COMMENT 'SKU',
    name        VARCHAR(128)  NOT NULL COMMENT '商品名称',
    category    VARCHAR(32)   NOT NULL COMMENT '类目',
    price       DECIMAL(12,2) NOT NULL COMMENT '售价（元）',
    stock       INT           NOT NULL DEFAULT 0 COMMENT '库存',
    status      TINYINT       NOT NULL DEFAULT 1 COMMENT '状态：1在售 0下架',
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_sku (sku),
    KEY idx_category (category)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='商品表';

CREATE TABLE IF NOT EXISTS task (
    id               BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    task_no          VARCHAR(32)  NOT NULL COMMENT '任务编号',
    title            VARCHAR(128) NOT NULL COMMENT '任务标题',
    related_order_no VARCHAR(32)  DEFAULT NULL COMMENT '关联订单号',
    status           VARCHAR(16)  NOT NULL COMMENT '任务状态：TODO/IN_PROGRESS/DONE/CANCELLED',
    owner            VARCHAR(64)  NOT NULL COMMENT '负责人',
    priority         TINYINT      NOT NULL DEFAULT 2 COMMENT '优先级：1高 2中 3低',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_task_no (task_no),
    KEY idx_status_owner (status, owner),
    KEY idx_related_order (related_order_no)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='任务表';

-- 会话消息历史（Context Engineering 的持久化载体）
CREATE TABLE IF NOT EXISTS agent_conversation (
    id         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_id VARCHAR(64)  NOT NULL COMMENT '会话ID',
    role       VARCHAR(16)  NOT NULL COMMENT '消息角色：system/user/assistant/tool',
    content    TEXT         COMMENT '消息内容',
    tool_calls JSON         COMMENT 'assistant 消息中的工具调用列表',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_session (session_id, id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='Agent 会话消息历史';

-- 每轮 LLM 调用追踪（Observability 地基）
CREATE TABLE IF NOT EXISTS agent_trace (
    id                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_id        VARCHAR(64)  NOT NULL COMMENT '会话ID',
    trace_id          VARCHAR(64)  NOT NULL COMMENT '追踪ID（一次完整 Agent 执行）',
    step              INT          NOT NULL DEFAULT 0 COMMENT 'Loop 步数',
    model             VARCHAR(64)  COMMENT '使用的模型',
    prompt_tokens     INT          COMMENT '输入 token 数',
    completion_tokens INT          COMMENT '输出 token 数',
    latency_ms        BIGINT       COMMENT '调用耗时（毫秒）',
    tool_names        VARCHAR(255) COMMENT '本步调用的工具名（逗号分隔）',
    request_body      MEDIUMTEXT   COMMENT '请求体（LLM 请求）',
    response_body     MEDIUMTEXT   COMMENT '响应体（LLM 响应）',
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_session (session_id, id),
    KEY idx_trace (trace_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='Agent 调用追踪';
