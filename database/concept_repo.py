"""
概念数据访问层
提供概念的增删改查操作，以及概念-事件关联操作
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

from models.concept import ConceptModel
from database.db import db


class ConceptRepository:
    """概念数据访问类"""
    
    def create(self, name: str) -> int:
        """
        创建新概念
        
        Args:
            name: 概念名称
            
        Returns:
            新创建概念的ID，如果已存在则返回现有ID
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 尝试插入新概念
            try:
                cursor.execute(
                    """
                    INSERT INTO concepts (name, last_activated, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (name, datetime.now().isoformat(), datetime.now().isoformat())
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # 概念已存在，返回现有ID
                cursor.execute("SELECT id FROM concepts WHERE name = ?", (name,))
                row = cursor.fetchone()
                return row["id"] if row else None
    
    def get_by_id(self, concept_id: int) -> Optional[ConceptModel]:
        """
        根据ID获取概念
        
        Args:
            concept_id: 概念ID
            
        Returns:
            概念模型对象
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM concepts WHERE id = ?", (concept_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return ConceptModel(
                id=row["id"],
                name=row["name"],
                last_activated=datetime.fromisoformat(row["last_activated"]),
                created_at=datetime.fromisoformat(row["created_at"])
            )
    
    def get_by_name(self, name: str) -> Optional[ConceptModel]:
        """
        根据名称获取概念
        
        Args:
            name: 概念名称
            
        Returns:
            概念模型对象
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM concepts WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return ConceptModel(
                id=row["id"],
                name=row["name"],
                last_activated=datetime.fromisoformat(row["last_activated"]),
                created_at=datetime.fromisoformat(row["created_at"])
            )
    
    def get_by_ids(self, concept_ids: List[int]) -> List[ConceptModel]:
        """
        根据ID列表获取多个概念
        
        Args:
            concept_ids: 概念ID列表
            
        Returns:
            概念模型列表
        """
        if not concept_ids:
            return []
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in concept_ids)
            cursor.execute(
                f"SELECT * FROM concepts WHERE id IN ({placeholders})",
                concept_ids
            )
            
            return [
                ConceptModel(
                    id=row["id"],
                    name=row["name"],
                    last_activated=datetime.fromisoformat(row["last_activated"]),
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in cursor.fetchall()
            ]
    
    def update_activation_time(self, concept_id: int) -> None:
        """
        更新概念的最后激活时间
        
        Args:
            concept_id: 概念ID
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE concepts SET last_activated = ? WHERE id = ?",
                (datetime.now().isoformat(), concept_id)
            )
    
    def get_recent_activated(self, limit: int = 10) -> List[ConceptModel]:
        """
        获取最近激活的概念
        
        Args:
            limit: 返回数量限制
            
        Returns:
            概念模型列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM concepts ORDER BY last_activated DESC LIMIT ?",
                (limit,)
            )
            
            return [
                ConceptModel(
                    id=row["id"],
                    name=row["name"],
                    last_activated=datetime.fromisoformat(row["last_activated"]),
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in cursor.fetchall()
            ]
    
    def link_event_concept(self, event_id: int, concept_id: int) -> None:
        """
        关联事件与概念
        
        Args:
            event_id: 事件ID
            concept_id: 概念ID
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO event_concepts (event_id, concept_id)
                VALUES (?, ?)
                """,
                (event_id, concept_id)
            )
    
    def get_event_concept_ids(self, event_id: int) -> List[int]:
        """
        获取事件关联的所有概念ID
        
        Args:
            event_id: 事件ID
            
        Returns:
            概念ID列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT concept_id FROM event_concepts WHERE event_id = ?",
                (event_id,)
            )
            return [row["concept_id"] for row in cursor.fetchall()]
    
    def get_concept_event_ids(self, concept_id: int) -> List[int]:
        """
        获取概念关联的所有事件ID
        
        Args:
            concept_id: 概念ID
            
        Returns:
            事件ID列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT event_id FROM event_concepts WHERE concept_id = ?",
                (concept_id,)
            )
            return [row["event_id"] for row in cursor.fetchall()]
    
    def batch_link_event_concepts(
        self, 
        event_id: int, 
        concept_ids: List[int]
    ) -> None:
        """
        批量关联事件与多个概念
        
        Args:
            event_id: 事件ID
            concept_ids: 概念ID列表
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for concept_id in concept_ids:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO event_concepts (event_id, concept_id)
                    VALUES (?, ?)
                    """,
                    (event_id, concept_id)
                )


# 全局概念仓储实例
concept_repo = ConceptRepository()
