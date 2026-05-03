"""
FAISS向量存储与检索
提供文本向量化、存储、相似度检索功能
"""

import json
import os
import numpy as np
from typing import List, Tuple, Optional
from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    FAISS_ID_MAP_PATH,
    ensure_dirs
)

import faiss


class VectorStore:
    """FAISS向量存储管理类"""
    
    def __init__(self, dimension: int = 1536):
        """
        初始化向量存储
        
        Args:
            dimension: 向量维度（OpenAI ada-002为1536维）
        """
        self.dimension = dimension
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        
        # ID映射：FAISS索引位置 -> 事件ID
        self.id_map: dict[int, int] = {}
        self.next_index: int = 0
        
        # 加载或创建FAISS索引
        self.index = self._load_or_create_index()
    
    def _load_or_create_index(self) -> faiss.IndexFlatIP:
        """
        加载已有索引或创建新索引
        
        Returns:
            FAISS索引对象
        """
        ensure_dirs()
        
        # 检查是否存在已有索引文件
        if FAISS_INDEX_PATH.exists() and FAISS_ID_MAP_PATH.exists():
            try:
                # 加载ID映射
                with open(FAISS_ID_MAP_PATH, "r", encoding="utf-8") as f:
                    saved_map = json.load(f)
                    self.id_map = {int(k): int(v) for k, v in saved_map.items()}
                    self.next_index = max(self.id_map.keys(), default=0) + 1
                
                # 加载FAISS索引
                index = faiss.read_index(str(FAISS_INDEX_PATH))
                print(f"[向量库] 加载已有索引，共{index.ntotal}条向量")
                return index
            except Exception as e:
                print(f"[向量库] 加载索引失败: {str(e)}，创建新索引")
        
        # 创建新索引（使用内积相似度）
        index = faiss.IndexFlatIP(self.dimension)
        print("[向量库] 创建新的FAISS索引")
        return index
    
    def save_index(self) -> None:
        """保存索引和ID映射到文件"""
        try:
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))
            
            with open(FAISS_ID_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(self.id_map, f, ensure_ascii=False, indent=2)
            
            print(f"[向量库] 索引已保存，共{self.index.ntotal}条向量")
        except Exception as e:
            print(f"[向量库] 保存索引失败: {str(e)}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            numpy数组格式的向量
        """
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            
            vector = response.data[0].embedding
            return np.array([vector], dtype=np.float32)
            
        except Exception as e:
            print(f"[向量生成失败] {str(e)}")
            # 返回随机向量作为备用（仅用于测试）
            print("[使用备用随机向量]")
            return np.random.randn(1, self.dimension).astype(np.float32)
    
    def add_vector(self, event_id: int, vector: np.ndarray) -> int:
        """
        添加向量到索引
        
        Args:
            event_id: 事件ID
            vector: 向量数组 (1, dimension)
            
        Returns:
            FAISS索引中的位置
        """
        # 归一化向量（用于内积相似度计算）
        faiss.normalize_L2(vector)
        
        # 添加到索引
        index_position = self.next_index
        self.index.add(vector)
        
        # 更新映射
        self.id_map[index_position] = event_id
        self.next_index += 1
        
        return index_position
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        相似度检索
        
        Args:
            query_vector: 查询向量 (1, dimension)
            top_k: 返回最相似的topK结果
            
        Returns:
            [(事件ID, 相似度分数), ...] 列表
        """
        if self.index.ntotal == 0:
            return []
        
        # 归一化查询向量
        faiss.normalize_L2(query_vector)
        
        # 执行搜索
        scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # 转换为(事件ID, 相似度)格式
        results = []
        for i in range(len(indices[0])):
            faiss_idx = indices[0][i]
            score = float(scores[0][i])
            
            if faiss_idx in self.id_map:
                event_id = self.id_map[faiss_idx]
                results.append((event_id, score))
        
        return results
    
    def get_event_id_by_index(self, faiss_index: int) -> Optional[int]:
        """
        根据FAISS索引位置获取事件ID
        
        Args:
            faiss_index: FAISS索引位置
            
        Returns:
            事件ID
        """
        return self.id_map.get(faiss_index)


# 全局向量存储实例
vector_store = VectorStore()
