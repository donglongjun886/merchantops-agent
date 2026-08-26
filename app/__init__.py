"""MerchantOps Agent 应用包。"""

import logging

# 让 AgentLoop 的日志在 uvicorn 下可见
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
