"""
概念数据模型
定义概念表的结构和操作方法
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ConceptModel(BaseModel):
    """概念数据模型"""
    
    id: Optional[int] = Field(default=None, description="概念ID")
    name: str = Field(..., description="概念名称")
    last_activated: datetime = Field(default_factory=datetime.now, description="最后激活时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "技术讨论",
                "last_activated": "2026-01-01T12:00:00",
                "created_at": "2026-01-01T12:00:00"
            }
        }
