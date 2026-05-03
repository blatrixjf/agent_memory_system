"""
抽象概念提取器
调用OpenAI兼容API从摘要中提取抽象概念
"""

from openai import OpenAI
from typing import List, Optional

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    CONCEPT_MODEL,
    CONCEPT_PROMPT
)


class ConceptExtractor:
    """抽象概念提取器"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
    
    def extract_concepts(self, summary: str) -> List[str]:
        """
        从摘要中提取抽象概念
        
        Args:
            summary: 对话摘要
            
        Returns:
            抽象概念列表（3-5个）
        """
        try:
            prompt = CONCEPT_PROMPT.format(summary=summary)
            
            response = self.client.chat.completions.create(
                model=CONCEPT_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的概念提取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            concepts_text = response.choices[0].message.content.strip()
            return self._parse_concepts(concepts_text)
            
        except Exception as e:
            print(f"[概念提取失败] {str(e)}")
            return self._fallback_extract(summary)
    
    def _parse_concepts(self, text: str) -> List[str]:
        """
        解析AI返回的概念文本
        
        Args:
            text: 概念文本（逗号分隔）
            
        Returns:
            清理后的概念列表
        """
        # 按逗号、顿号、换行符分割
        separators = [",", "，", "、", "\n"]
        
        for sep in separators:
            if sep in text:
                concepts = [c.strip() for c in text.split(sep)]
                return [c for c in concepts if c and len(c) > 0][:5]
        
        # 如果没有分隔符，直接返回原文本
        return [text] if text else []
    
    def _fallback_extract(self, summary: str) -> List[str]:
        """
        备用概念提取方法（当API不可用时）
        
        Args:
            summary: 对话摘要
            
        Returns:
            简单的规则提取概念
        """
        # 简单的关键词提取规则
        fallback_concepts = []
        
        keywords = {
            "Python": "编程学习",
            "代码": "编程实践",
            "算法": "算法设计",
            "数据": "数据处理",
            "数据库": "数据存储",
            "API": "接口开发",
            "函数": "编程基础",
            "类": "面向对象",
            "配置": "系统配置",
            "测试": "软件测试",
        }
        
        for keyword, concept in keywords.items():
            if keyword.lower() in summary.lower():
                fallback_concepts.append(concept)
        
        if not fallback_concepts:
            fallback_concepts = ["日常对话"]
        
        return fallback_concepts[:5]


# 全局概念提取器实例
concept_extractor = ConceptExtractor()
