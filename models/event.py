"""
事件数据模型
定义事件表的结构和操作方法
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EventModel(BaseModel):
    """事件数据模型"""
    
    id: Optional[int] = Field(default=None, description="事件ID")
    user_message: str = Field(..., description="用户消息内容")
    ai_reply: str = Field(..., description="AI回复内容")
    summary: str = Field(..., description="一句话摘要")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_message": "你好，我想了解一下Python",
                "ai_reply": "Python是一门很流行的编程语言...",
                "summary": "用户询问Python编程语言",
                "timestamp": "2026-01-01T12:00:00"
            }
        }
