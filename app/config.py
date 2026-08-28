"""应用配置：从环境变量 / .env 读取。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore"：.env 里多余的变量（如 DASHSCOPE_API_KEY）不报错
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048
    llm_max_steps: int = 10
    # 同步驱动 PyMySQL，连 docker-compose 起的 MySQL 8.0
    database_url: str = "mysql+pymysql://merchantops:merchantops@127.0.0.1:3306/merchantops?charset=utf8mb4"


settings = Settings()
