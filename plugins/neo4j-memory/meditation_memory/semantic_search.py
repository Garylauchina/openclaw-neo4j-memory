"""
记忆系统语义搜索兜底模块（P0-4）

当精确匹配和模糊搜索失败时，使用语义相似度找到相关实体。
支持两种模式：
  1. 外部 embedding API（OpenAI 格式）— 需要配置
  2. 本地 TF-IDF + 余弦相似度（无外部依赖，保底方案）

使用方式：
  semantic = SemanticSearch(graph_store, config)
  candidates = semantic.find_similar(query="股票价格", candidate_names=["股价", "股票", "涨跌"])
"""

import hashlib
import logging
import math
import os
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass, field

from .config import LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Embedding 服务配置"""
    enabled: bool = False
    # 外部 API 配置
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "text-embedding-3-small"
    # 本地 TF-IDF 配置
    use_local_tfidf: bool = True
    tfidf_vocab_size: int = 5000
    # 缓存
    cache_enabled: bool = True
    max_cache_size: int = 1000


class LocalTFIDF:
    """本地 TF-IDF 向量化，无需外部依赖"""
    
    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = vocab_size
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None
        self.fitted = False
    
    def build_vocab(self, documents: List[str]) -> None:
        """从文档集合构建词汇表（按词频选择前 vocab_size 个词）"""
        from collections import Counter
        import jieba
        
        word_counter = Counter()
        for doc in documents:
            # 中文分词
            words = list(jieba.cut(doc, cut_all=False))
            word_counter.update(words)
        
        # 按词频排序，选取前 vocab_size
        common_words = [word for word, _ in word_counter.most_common(self.vocab_size)]
        self.vocab = {word: i for i, word in enumerate(common_words)}
        
        # 计算 IDF
        doc_count = len(documents)
        doc_has_word = np.zeros((self.vocab_size,))
        
        for doc in documents:
            words = set(jieba.cut(doc, cut_all=False))
            doc_vector = np.zeros((self.vocab_size,))
            for word in words:
                if word in self.vocab:
                    doc_has_word[self.vocab[word]] += 1
            
        # IDF = log(总文档数 / 包含该词的文档数)
        self.idf = np.log(doc_count / (doc_has_word + 1e-10))
        self.fitted = True
        logger.info(f"LocalTFIDF 词汇表构建完成，大小: {len(self.vocab)}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """将文本转换为 TF-IDF 向量"""
        import jieba
        from collections import Counter
        
        if not self.fitted or len(self.vocab) == 0:
            # 回退：简单的词袋向量
            return self._fallback_bow(text)
        
        words = list(jieba.cut(text, cut_all=False))
        word_counts = Counter(words)
        
        # TF 向量
        tf_vector = np.zeros((self.vocab_size,))
        total_words = len(words) if words else 1
        
        for word, count in word_counts.items():
            if word in self.vocab:
                idx = self.vocab[word]
                tf_vector[idx] = count / total_words
        
        # TF-IDF = TF * IDF
        tfidf = tf_vector * self.idf
        # L2 归一化
        norm = np.linalg.norm(tfidf)
        if norm > 0:
            tfidf = tfidf / norm
        
        return tfidf
    
    def _fallback_bow(self, text: str) -> np.ndarray:
        """简单的回退词袋表示"""
        words = set(text)  # 字符级别
        vec = np.zeros((self.vocab_size,))
        for i, char in enumerate(words):
            if i < self.vocab_size:
                vec[i] = 1
        return vec / max(np.linalg.norm(vec), 1e-10)


class SemanticSearch:
    """语义搜索服务"""
    
    def __init__(self, graph_store, config: Optional[EmbeddingConfig] = None):
        self.store = graph_store
        self.config = config or EmbeddingConfig()
        self.cache: Dict[str, np.ndarray] = {}
        
        # 本地 TF-IDF 初始化
        if self.config.use_local_tfidf:
            self.tfidf = LocalTFIDF(self.config.tfidf_vocab_size)
            self._need_fit = True  # 首次使用时才拟合
        else:
            self.tfidf = None
        
        # 外部 embedding 客户端（懒加载）
        self._api_client = None
        
        logger.info(f"SemanticSearch 初始化完成，使用外部 API: {self.config.enabled}, 本地 TF-IDF: {self.config.use_local_tfidf}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的 embedding 向量"""
        # 缓存
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        if self.config.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]
        
        # 优先外部 API
        if self.config.enabled and self.config.api_key:
            vec = self._get_api_embedding(text)
        else:
            # 本地 TF-IDF
            vec = self._get_local_embedding(text)
        
        # 缓存
        if self.config.cache_enabled:
            if len(self.cache) >= self.config.max_cache_size:
                # LRU 简单策略：清空缓存
                self.cache.clear()
            self.cache[cache_key] = vec
        
        return vec
    
    def _get_api_embedding(self, text: str) -> np.ndarray:
        """调用外部 embedding API"""
        try:
            import openai
            if self._api_client is None:
                openai.api_key = self.config.api_key
                if self.config.base_url:
                    openai.base_url = self.config.base_url
                self._api_client = openai
            
            resp = self._api_client.embeddings.create(
                model=self.config.model,
                input=text,
                encoding_format="float"
            )
            return np.array(resp.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.warning(f"外部 embedding API 失败，回退到本地 TF-IDF: {e}")
            return self._get_local_embedding(text)
    
    def _get_local_embedding(self, text: str) -> np.ndarray:
        """本地 TF-IDF embedding"""
        if self.tfidf is None:
            # 回退：简单的 one-hot 向量
            return self._simple_char_embedding(text)
        
        if self._need_fit:
            # 从数据库获取一些文档来拟合 TF-IDF
            self._fit_tfidf()
        
        return self.tfidf.get_embedding(text)
    
    def _fit_tfidf(self):
        """从数据库中采样文档拟合 TF-IDF"""
        try:
            # 获取一些实体名称作为训练数据
            docs = self._fetch_entity_names()
            if len(docs) < 10:
                docs.extend(["记忆系统", "实体", "关系", "用户", "对话", "人工智能", "深度学习", "机器学习"])
            
            self.tfidf.build_vocab(docs)
            self._need_fit = False
        except Exception as e:
            logger.warning(f"TF-IDF 拟合失败，使用回退模式: {e}")
    
    def _fetch_entity_names(self, limit: int = 1000) -> List[str]:
        """从数据库中获取实体名称作为训练样本"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
        RETURN e.name
        LIMIT $limit
        """
        try:
            with self.store.driver.session(database=self.store._config.database) as session:
                result = session.run(query, limit=limit)
                return [record["e.name"] for record in result]
        except Exception:
            return []
    
    def _simple_char_embedding(self, text: str) -> np.ndarray:
        """简单的字符级 one-hot（回退）"""
        chars = set(text)
        vec = np.zeros((256,))  # 简单 ASCII 表示
        for i, char in enumerate(chars):
            if i < 256:
                code = ord(char) % 256
                vec[code] = 1
        return vec / max(np.linalg.norm(vec), 1e-10)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """余弦相似度"""
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def find_similar(
        self, 
        query: str, 
        candidate_names: List[str], 
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        在候选名称中查找与查询语义相似的实体
        
        返回: [(实体名, 相似度), ...]
        """
        if not candidate_names:
            return []
        
        query_vec = self.get_embedding(query)
        
        similarities = []
        for name in candidate_names:
            name_vec = self.get_embedding(name)
            sim = self.cosine_similarity(query_vec, name_vec)
            if sim >= min_similarity:
                similarities.append((name, float(sim)))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def search_in_database(
        self, 
        query: str, 
        limit: int = 10, 
        min_similarity: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        在整个数据库中搜索语义相似的实体
        
        返回: [{"name": ..., "similarity": ...}, ...]
        """
        try:
            # 获取候选实体
            candidate_names = self._fetch_entity_names(limit=1000)  # 限制候选集
            if not candidate_names:
                return []
            
            similar_items = self.find_similar(
                query, candidate_names, 
                top_k=limit, min_similarity=min_similarity
            )
            
            return [
                {"name": name, "similarity": sim}
                for name, sim in similar_items
            ]
        except Exception as e:
            logger.error(f"语义数据库搜索失败: {e}")
            return []