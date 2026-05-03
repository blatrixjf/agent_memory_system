"""
事件数据访问层
提供事件的增删改查操作
"""

import sqlite3
from datetime import datetime
from typing import Optional, List

from models.event import EventModel
from database.db import db


class EventRepository:
    """事件数据访问类"""
    
    def create(self, event: EventModel) -> int:
        """
        创建新事件
        
        Args:
            event: 事件模型对象
            
        Returns:
            新创建事件的ID
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO events (user_message, ai_reply, summary, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.user_message,
                    event.ai_reply,
                    event.summary,
                    event.timestamp.isoformat()
                )
            )
            return cursor.lastrowid
    
    def get_by_id(self, event_id: int) -> Optional[EventModel]:
        """
        根据ID获取事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            事件模型对象，如果不存在则返回None
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return EventModel(
                id=row["id"],
                user_message=row["user_message"],
                ai_reply=row["ai_reply"],
                summary=row["summary"],
                timestamp=datetime.fromisoformat(row["timestamp"])
            )
    
    def get_all(self, limit: int = 100) -> List[EventModel]:
        """
        获取所有事件（按时间倒序）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            事件模型列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            
            return [
                EventModel(
                    id=row["id"],
                    user_message=row["user_message"],
                    ai_reply=row["ai_reply"],
                    summary=row["summary"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                for row in cursor.fetchall()
            ]
    
    def get_latest_by_concept(self, concept_id: int) -> Optional[EventModel]:
        """
        获取指定概念下最新的事件
        
        Args:
            concept_id: 概念ID
            
        Returns:
            最新的事件模型对象
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.* FROM events e
                INNER JOIN event_concepts ec ON e.id = ec.event_id
                WHERE ec.concept_id = ?
                ORDER BY e.timestamp DESC
                LIMIT 1
                """,
                (concept_id,)
            )
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return EventModel(
                id=row["id"],
                user_message=row["user_message"],
                ai_reply=row["ai_reply"],
                summary=row["summary"],
                timestamp=datetime.fromisoformat(row["timestamp"])
            )
    
    def get_older_by_concept(
        self, 
        concept_id: int, 
        exclude_event_id: int, 
        limit: int = 3
    ) -> List[EventModel]:
        """
        获取指定概念下的历史事件（排除指定事件）
        
        Args:
            concept_id: 概念ID
            exclude_event_id: 要排除的事件ID
            limit: 返回数量限制
            
        Returns:
            历史事件模型列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.* FROM events e
                INNER JOIN event_concepts ec ON e.id = ec.event_id
                WHERE ec.concept_id = ? AND e.id != ?
                ORDER BY e.timestamp DESC
                LIMIT ?
                """,
                (concept_id, exclude_event_id, limit)
            )
            
            return [
                EventModel(
                    id=row["id"],
                    user_message=row["user_message"],
                    ai_reply=row["ai_reply"],
                    summary=row["summary"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                for row in cursor.fetchall()
            ]
    
    def get_by_ids(self, event_ids: List[int]) -> List[EventModel]:
        """
        根据ID列表获取多个事件
        
        Args:
            event_ids: 事件ID列表
            
        Returns:
            事件模型列表
        """
        if not event_ids:
            return []
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in event_ids)
            cursor.execute(
                f"SELECT * FROM events WHERE id IN ({placeholders})",
                event_ids
            )
            
            return [
                EventModel(
                    id=row["id"],
                    user_message=row["user_message"],
                    ai_reply=row["ai_reply"],
                    summary=row["summary"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                for row in cursor.fetchall()
            ]
    
    def count(self) -> int:
        """
        获取事件总数
        
        Returns:
            事件总数
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM events")
            return cursor.fetchone()["count"]


# 全局事件仓储实例
event_repo = EventRepository()
