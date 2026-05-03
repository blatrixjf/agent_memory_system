"""
记忆管理器
核心记忆逻辑：事件处理、检索、召回、懒加载
"""

from typing import List, Optional, Tuple
from datetime import datetime

from config import (
    SIMILARITY_THRESHOLD,
    TOP_K_CONCEPTS,
    MAX_LAZY_LOAD_COUNT,
    MAX_CONTEXT_TOKENS,
    ESTIMATED_TOKENS_PER_EVENT,
    LAZY_LOAD_TRIGGER_WORDS
)

from models.event import EventModel
from models.concept import ConceptModel
from memory.summarizer import summarizer
from memory.concept_extractor import concept_extractor
from memory.vector_store import vector_store
from database.event_repo import event_repo
from database.concept_repo import concept_repo


class MemoryManager:
    """记忆系统核心管理类"""
    
    def __init__(self):
        """初始化记忆管理器"""
        pass
    
    def process_new_event(
        self,
        user_message: str,
        ai_reply: str
    ) -> Tuple[int, List[str]]:
        """
        处理新对话事件：摘要→概念→向量→入库
        
        Args:
            user_message: 用户消息
            ai_reply: AI回复
            
        Returns:
            (事件ID, 概念名称列表)
        """
        print("\n[记忆处理] 开始处理新事件...")
        
        # 步骤1：生成摘要
        print("[记忆处理] 步骤1: 生成对话摘要...")
        summary = summarizer.generate_summary(user_message, ai_reply)
        print(f"[记忆处理] 摘要: {summary}")
        
        # 步骤2：提取抽象概念
        print("[记忆处理] 步骤2: 提取抽象概念...")
        concept_names = concept_extractor.extract_concepts(summary)
        print(f"[记忆处理] 概念: {concept_names}")
        
        # 步骤3：创建事件并入库
        event = EventModel(
            user_message=user_message,
            ai_reply=ai_reply,
            summary=summary,
            timestamp=datetime.now()
        )
        event_id = event_repo.create(event)
        print(f"[记忆处理] 步骤3: 事件已入库，ID={event_id}")
        
        # 步骤4：创建概念并建立关联
        concept_ids = []
        for name in concept_names:
            concept_id = concept_repo.create(name)
            if concept_id:
                concept_repo.link_event_concept(event_id, concept_id)
                concept_ids.append(concept_id)
                # 更新激活时间
                concept_repo.update_activation_time(concept_id)
        
        print(f"[记忆处理] 步骤4: 概念关联完成，共{len(concept_ids)}个概念")
        
        # 步骤5：生成向量并存入FAISS
        print("[记忆处理] 步骤5: 生成向量...")
        vector = vector_store.embed_text(summary)
        vector_store.add_vector(event_id, vector)
        print("[记忆处理] 步骤5: 向量已存入")
        
        # 步骤6：保存向量索引
        vector_store.save_index()
        
        return event_id, concept_names
    
    def retrieve_recent_memory(
        self,
        user_message: str
    ) -> Optional[EventModel]:
        """
        检索最近记忆：根据新对话召回最相似概念下的最近1条事件
        
        Args:
            user_message: 用户新消息
            
        Returns:
            最近的相关事件，如果没有找到则返回None
        """
        print("\n[记忆检索] 开始检索相关记忆...")
        
        # 步骤1：为当前消息生成向量
        query_vector = vector_store.embed_text(user_message)
        
        # 步骤2：向量相似度检索
        results = vector_store.search(query_vector, top_k=TOP_K_CONCEPTS)
        
        if not results:
            print("[记忆检索] 未找到相似记忆")
            return None
        
        # 步骤3：按相似度过滤并获取最相似的事件
        for event_id, similarity in results:
            if similarity >= SIMILARITY_THRESHOLD:
                # 获取该事件的详细信息
                event = event_repo.get_by_id(event_id)
                if event:
                    print(f"[记忆检索] 找到相似记忆 (相似度={similarity:.2f}): {event.summary}")
                    
                    # 更新关联概念的激活时间
                    concept_ids = concept_repo.get_event_concept_ids(event_id)
                    for concept_id in concept_ids:
                        concept_repo.update_activation_time(concept_id)
                    
                    return event
        
        print("[记忆检索] 相似度低于阈值，未召回记忆")
        return None
    
    def lazy_load_older_memory(
        self,
        reference_event_id: int,
        max_count: Optional[int] = None
    ) -> List[EventModel]:
        """
        懒加载久远记忆：从相同概念下加载更多历史事件
        
        Args:
            reference_event_id: 参考事件ID（最近召回的事件）
            max_count: 最多加载条数（默认使用配置值）
            
        Returns:
            历史事件列表
        """
        limit = max_count or MAX_LAZY_LOAD_COUNT
        
        print(f"\n[懒加载] 开始加载久远记忆，参考事件ID={reference_event_id}...")
        
        # 获取参考事件关联的概念
        concept_ids = concept_repo.get_event_concept_ids(reference_event_id)
        
        if not concept_ids:
            print("[懒加载] 该事件没有关联概念")
            return []
        
        # 计算最多加载条数（考虑Token限制）
        max_by_tokens = MAX_CONTEXT_TOKENS // ESTIMATED_TOKENS_PER_EVENT
        limit = min(limit, max_by_tokens)
        
        # 从所有关联概念中加载历史事件
        older_events = []
        for concept_id in concept_ids:
            events = concept_repo.get_concept_event_ids(concept_id)
            
            # 获取具体事件详情
            event_details = event_repo.get_older_by_concept(
                concept_id=concept_id,
                exclude_event_id=reference_event_id,
                limit=limit
            )
            
            older_events.extend(event_details)
        
        # 去重并按时间排序
        seen_ids = set()
        unique_events = []
        for event in older_events:
            if event.id not in seen_ids:
                seen_ids.add(event.id)
                unique_events.append(event)
        
        # 按时间倒序（最近的在前）
        unique_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # 限制返回数量
        result = unique_events[:limit]
        
        print(f"[懒加载] 加载了{len(result)}条久远记忆")
        return result
    
    def should_trigger_lazy_load(self, user_message: str) -> bool:
        """
        判断是否应该触发懒加载
        
        Args:
            user_message: 用户消息
            
        Returns:
            是否触发懒加载
        """
        message_lower = user_message.lower()
        
        # 检查是否包含触发关键词
        for trigger_word in LAZY_LOAD_TRIGGER_WORDS:
            if trigger_word in message_lower:
                return True
        
        return False
    
    def format_memory_context(
        self,
        recent_event: Optional[EventModel],
        older_events: Optional[List[EventModel]] = None
    ) -> str:
        """
        格式化记忆上下文用于AI对话
        
        Args:
            recent_event: 最近的相关事件
            older_events: 久远记忆列表
            
        Returns:
            格式化的记忆上下文字符串
        """
        context_parts = []
        
        # 添加最近记忆
        if recent_event:
            context_parts.append(
                f"[最近相关记忆] 我们之前聊过：{recent_event.summary}"
            )
        
        # 添加久远记忆
        if older_events:
            context_parts.append("\n[久远记忆]")
            for i, event in enumerate(older_events, 1):
                context_parts.append(
                    f"{i}. {event.summary} (时间: {event.timestamp.strftime('%Y-%m-%d %H:%M')})"
                )
        
        return "\n".join(context_parts)


# 全局记忆管理器实例
memory_manager = MemoryManager()
