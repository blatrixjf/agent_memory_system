"""
SQLite数据库连接与表创建
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from config import DB_PATH, ensure_dirs


class Database:
    """数据库连接管理类"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """初始化数据库连接"""
        self.db_path = db_path or DB_PATH
        ensure_dirs()
        self._init_tables()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_tables(self) -> None:
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    ai_reply TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建概念表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    last_activated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建事件-概念关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    concept_id INTEGER NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
                    UNIQUE(event_id, concept_id)
                )
            """)
            
            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_concepts_last_activated 
                ON concepts(last_activated DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_concepts_event_id 
                ON event_concepts(event_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_concepts_concept_id 
                ON event_concepts(concept_id)
            """)


# 全局数据库实例
db = Database()
