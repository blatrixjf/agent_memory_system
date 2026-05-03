"""
摘要生成器
调用OpenAI兼容API生成对话摘要
"""

from openai import OpenAI
from typing import Optional

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    SUMMARY_MODEL,
    SUMMARY_PROMPT
)


class Summarizer:
    """对话摘要生成器"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
    
    def generate_summary(
        self,
        user_message: str,
        ai_reply: str
    ) -> Optional[str]:
        """
        生成对话摘要
        
        Args:
            user_message: 用户消息
            ai_reply: AI回复
            
        Returns:
            一句话摘要，失败返回None
        """
        try:
            prompt = SUMMARY_PROMPT.format(
                user_message=user_message,
                ai_reply=ai_reply
            )
            
            response = self.client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的对话摘要生成器。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"[摘要生成失败] {str(e)}")
            # 如果API调用失败，使用简单规则生成摘要
            return self._fallback_summary(user_message)
    
    def _fallback_summary(self, user_message: str) -> str:
        """
        备用摘要生成方法（当API不可用时）
        
        Args:
            user_message: 用户消息
            
        Returns:
            简单的规则摘要
        """
        # 截取前50个字符作为简单摘要
        if len(user_message) > 50:
            return user_message[:47] + "..."
        return user_message


# 全局摘要生成器实例
summarizer = Summarizer()
