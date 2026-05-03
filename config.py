"""
配置文件 - 智能体记忆系统
包含OpenAI API配置、数据库路径、相似度阈值等
"""

import os
from pathlib import Path

# ============ OpenAI API配置 ============
# 可替换为任何OpenAI兼容接口（如本地模型、第三方代理等）
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your-api-key-here")
OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# 模型配置
EMBEDDING_MODEL: str = "text-embedding-ada-002"  # 向量嵌入模型
SUMMARY_MODEL: str = "gpt-3.5-turbo"              # 摘要生成模型
CONCEPT_MODEL: str = "gpt-3.5-turbo"              # 概念提取模型
CHAT_MODEL: str = "gpt-3.5-turbo"                 # 对话模型

# ============ 数据库配置 ============
# SQLite数据库文件路径
DB_DIR: Path = Path(__file__).parent / "data"
DB_PATH: Path = DB_DIR / "memory.db"

# ============ FAISS向量库配置 ============
# FAISS索引文件路径
FAISS_INDEX_DIR: Path = Path(__file__).parent / "data" / "faiss"
FAISS_INDEX_PATH: Path = FAISS_INDEX_DIR / "index.faiss"
FAISS_ID_MAP_PATH: Path = FAISS_INDEX_DIR / "id_map.json"

# ============ 记忆检索配置 ============
# 向量相似度阈值（余弦相似度，0-1之间）
SIMILARITY_THRESHOLD: float = 0.75

# 检索时返回的最相似概念数量
TOP_K_CONCEPTS: int = 5

# 懒加载时最多加载的久远记忆条数
MAX_LAZY_LOAD_COUNT: int = 3

# 最大上下文Token限制（用于控制加载的记忆条数）
MAX_CONTEXT_TOKENS: int = 4000

# 单条事件估算Token数（用于计算可加载条数）
ESTIMATED_TOKENS_PER_EVENT: int = 100

# ============ 提示词配置 ============
# 摘要生成提示词
SUMMARY_PROMPT: str = """
请将以下对话内容总结为一句话摘要，要求：
1. 简洁明了，不超过30个字
2. 保留核心话题和关键信息
3. 使用陈述句

对话内容：
用户：{user_message}
AI：{ai_reply}

摘要：
"""

# 抽象概念提取提示词
CONCEPT_PROMPT: str = """
请从以下摘要中提取3-5个抽象概念或关键词，要求：
1. 概念要抽象且具有概括性（如"技术讨论"、"情感表达"、"计划安排"）
2. 用逗号分隔
3. 不要包含具体的人名、地名等专有名词
4. 每个概念2-6个字

摘要：{summary}

抽象概念：
"""

# ============ 懒加载触发关键词 ============
# 用户回复这些词时触发久远记忆加载
LAZY_LOAD_TRIGGER_WORDS: list[str] = [
    "不是", "不对", "没有", "没聊过", "不认识",
    "更早", "上次", "之前", "以前的",
    "详细", "全部", "所有", "更多"
]

# ============ 工具函数 ============
def ensure_dirs() -> None:
    """确保所有必要的目录存在"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
