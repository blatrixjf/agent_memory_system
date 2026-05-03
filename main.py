"""
入口文件 - 智能体记忆系统对话循环
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from typing import Optional

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    CHAT_MODEL
)
from memory.memory_manager import memory_manager
from memory.vector_store import vector_store


class AgentMemorySystem:
    """智能体记忆系统主类"""
    
    def __init__(self):
        """初始化系统"""
        print("=" * 50)
        print("  智能体记忆系统 v1.0")
        print("=" * 50)
        
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        
        # 对话历史（仅保存当前会话的上下文）
        self.chat_history = []
    
    def generate_ai_reply(
        self,
        user_message: str,
        memory_context: Optional[str] = None
    ) -> str:
        """
        生成AI回复
        
        Args:
            user_message: 用户消息
            memory_context: 记忆上下文（可选）
            
        Returns:
            AI回复内容
        """
        try:
            # 构建系统提示词
            system_prompt = "你是一个有帮助的AI助手。"
            
            if memory_context:
                system_prompt += f"\n\n以下是相关的历史记忆：\n{memory_context}"
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 添加历史对话（最近5轮）
            messages.extend(self.chat_history[-10:])
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 调用AI生成回复
            response = self.client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"[AI回复生成失败] {str(e)}")
            return f"[系统] AI回复生成失败：{str(e)}"
    
    def process_conversation(self, user_message: str) -> str:
        """
        处理一轮对话
        
        Args:
            user_message: 用户消息
            
        Returns:
            AI回复内容
        """
        # 步骤1：检索相关记忆
        recent_memory = memory_manager.retrieve_recent_memory(user_message)
        
        # 步骤2：构建记忆上下文
        memory_context = None
        question_to_user = None
        
        if recent_memory:
            memory_context = memory_manager.format_memory_context(recent_memory)
            question_to_user = f"\n\n[系统] 我们之前是不是聊过【{recent_memory.summary}】？"
        
        # 步骤3：生成AI回复
        ai_reply = self.generate_ai_reply(user_message, memory_context)
        
        # 步骤4：检查是否触发懒加载
        older_memories = []
        if recent_memory and memory_manager.should_trigger_lazy_load(user_message):
            older_memories = memory_manager.lazy_load_older_memory(recent_memory.id)
            
            if older_memories:
                # 重新构建包含久远记忆的上下文
                memory_context = memory_manager.format_memory_context(
                    recent_memory,
                    older_memories
                )
                # 重新生成回复（包含更完整的记忆）
                ai_reply = self.generate_ai_reply(user_message, memory_context)
        
        # 步骤5：处理新事件（存入记忆）
        event_id, concepts = memory_manager.process_new_event(
            user_message,
            ai_reply
        )
        
        # 步骤6：更新对话历史
        self.chat_history.append({"role": "user", "content": user_message})
        self.chat_history.append({"role": "assistant", "content": ai_reply})
        
        # 步骤7：构建输出
        output = ai_reply
        
        if question_to_user and not memory_manager.should_trigger_lazy_load(user_message):
            output += question_to_user
        
        if older_memories:
            output += "\n\n[系统] 已为您加载了更多历史记忆。"
        
        return output
    
    def run(self):
        """运行对话循环"""
        print("\n欢迎使用智能体记忆系统！")
        print("输入 'quit' 或 'exit' 退出程序")
        print("输入 'history' 查看记忆统计")
        print("输入 'clear' 清空对话历史\n")
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["quit", "exit"]:
                    print("\n再见！")
                    break
                
                if user_input.lower() == "history":
                    self.show_history_stats()
                    continue
                
                if user_input.lower() == "clear":
                    self.chat_history = []
                    print("[系统] 对话历史已清空")
                    continue
                
                # 处理对话
                print("\n[思考中...]")
                ai_reply = self.process_conversation(user_input)
                print(f"\nAI: {ai_reply}\n")
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n[错误] {str(e)}\n")
    
    def show_history_stats(self):
        """显示记忆统计信息"""
        from database.event_repo import event_repo
        from database.concept_repo import concept_repo
        
        event_count = event_repo.count()
        print(f"\n[记忆统计]")
        print(f"  - 事件总数: {event_count}")
        print(f"  - 向量库大小: {vector_store.index.ntotal}")
        print()


def main():
    """主函数"""
    system = AgentMemorySystem()
    system.run()


if __name__ == "__main__":
    main()
