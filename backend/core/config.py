import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # NOTE: 大模型配置 — 仅使用 Moonshot / Kimi
    LLM_PROVIDER: str = "moonshot"
    LLM_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    LLM_API_BASE: str = os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.cn/v1")
    LLM_MODEL: str = os.getenv("MOONSHOT_MODEL", "moonshot-v1-32k")
    
    # JWT 认证配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-环保署-豆沙包-教师助手")

settings = Settings()

