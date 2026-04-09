"""
提示词熵（Prompt Entropy）计算模块 - Issue #54

衡量构建好的提示词（上下文）的信息不确定性/复杂度，与图谱熵形成双向闭环。

功能：
1. Token-level Entropy - 基于词频分布的 Shannon 熵（近似）
2. Semantic Entropy - 基于语义聚类的熵（需要 embedding）
3. Prompt Perplexity - 简化版困惑度计算
4. 提示词熵健康报告生成

信息论闭环：
Meditation 降低图谱熵 → 产生更低熵的提示词 → 用提示词熵反馈优化 Meditation
"""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class PromptEntropyResult:
    """提示词熵计算结果"""
    # Token-level 指标
    token_entropy: float = 0.0  # Shannon 熵 (bits)
    token_perplexity: float = 0.0  # 困惑度 = 2^entropy
    vocabulary_size: int = 0  # 词表大小
    total_tokens: int = 0  # 总 token 数
    
    # Semantic 指标（如果有 embedding）
    semantic_entropy: Optional[float] = None  # 语义熵
    semantic_clusters: int = 0  # 语义簇数量
    
    # 统计信息
    unique_token_ratio: float = 0.0  # 唯一 token 比例
    repetition_ratio: float = 0.0  # 重复 token 比例
    information_density: float = 0.0  # 信息密度 = entropy / max_entropy
    
    # 健康评估
    health_score: float = 0.0  # 0-1，越高越好
    health_level: str = "unknown"  # "excellent", "good", "fair", "poor"
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_entropy": round(self.token_entropy, 4),
            "token_perplexity": round(self.token_perplexity, 4),
            "vocabulary_size": self.vocabulary_size,
            "total_tokens": self.total_tokens,
            "semantic_entropy": round(self.semantic_entropy, 4) if self.semantic_entropy else None,
            "semantic_clusters": self.semantic_clusters,
            "unique_token_ratio": round(self.unique_token_ratio, 4),
            "repetition_ratio": round(self.repetition_ratio, 4),
            "information_density": round(self.information_density, 4),
            "health_score": round(self.health_score, 4),
            "health_level": self.health_level,
            "recommendations": self.recommendations
        }


class PromptEntropyCalculator:
    """
    提示词熵计算器
    
    支持多种熵计算方式：
    1. Token-level Shannon Entropy
    2. Semantic Entropy（需要 embedding 支持）
    3. Perplexity（困惑度）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # 熵计算配置
        self.max_expected_entropy = self.config.get("max_expected_entropy", 10.0)  # 最大期望熵值
        self.entropy_threshold_high = self.config.get("entropy_threshold_high", 0.7)  # 高熵阈值
        self.entropy_threshold_low = self.config.get("entropy_threshold_low", 0.3)  # 低熵阈值
        
    def calculate_token_entropy(self, text: str) -> PromptEntropyResult:
        """
        计算 Token-level Shannon 熵
        
        基于词频分布计算：H = -Σ p(x) * log2(p(x))
        
        Args:
            text: 提示词文本
            
        Returns:
            PromptEntropyResult 包含熵值和相关指标
        """
        # 1. 分词（简化版：按空格和标点分割）
        tokens = self._tokenize(text)
        total_tokens = len(tokens)
        
        if total_tokens == 0:
            return PromptEntropyResult(
                health_level="poor",
                health_score=0.0,
                recommendations=["提示词为空，无法计算熵"]
            )
        
        # 2. 计算词频分布
        token_counts = Counter(tokens)
        vocabulary_size = len(token_counts)
        
        # 3. 计算 Shannon 熵
        entropy = 0.0
        for count in token_counts.values():
            probability = count / total_tokens
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # 4. 计算困惑度 (Perplexity)
        perplexity = 2 ** entropy
        
        # 5. 计算其他指标
        unique_token_ratio = vocabulary_size / total_tokens
        repetition_ratio = 1.0 - unique_token_ratio
        
        # 6. 计算信息密度（归一化熵）
        max_entropy = math.log2(vocabulary_size) if vocabulary_size > 1 else 1.0
        information_density = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # 7. 健康评估
        health_score, health_level, recommendations = self._evaluate_health(
            entropy=entropy,
            information_density=information_density,
            unique_token_ratio=unique_token_ratio,
            total_tokens=total_tokens
        )
        
        result = PromptEntropyResult(
            token_entropy=entropy,
            token_perplexity=perplexity,
            vocabulary_size=vocabulary_size,
            total_tokens=total_tokens,
            unique_token_ratio=unique_token_ratio,
            repetition_ratio=repetition_ratio,
            information_density=information_density,
            health_score=health_score,
            health_level=health_level,
            recommendations=recommendations
        )
        
        logger.info(
            f"Token 熵计算完成：entropy={entropy:.4f}, perplexity={perplexity:.4f}, "
            f"vocabulary={vocabulary_size}, tokens={total_tokens}, health={health_level}"
        )
        
        return result
    
    def calculate_semantic_entropy(
        self, 
        text: str, 
        embeddings: Optional[List[List[float]]] = None
    ) -> PromptEntropyResult:
        """
        计算 Semantic Entropy（语义熵）
        
        基于语义聚类的熵：
        1. 将文本分成语义单元（句子/段落）
        2. 计算每个单元的 embedding
        3. 聚类语义单元
        4. 计算簇分布的熵
        
        Args:
            text: 提示词文本
            embeddings: 预计算的 embedding 列表（可选）
            
        Returns:
            PromptEntropyResult 包含语义熵
        """
        # 1. 分割文本为语义单元（句子）
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return PromptEntropyResult(
                semantic_entropy=0.0,
                semantic_clusters=0,
                recommendations=["无法分割句子，无法计算语义熵"]
            )
        
        # 2. 如果有 embeddings，使用聚类计算语义熵
        if embeddings and len(embeddings) == len(sentences):
            clusters = self._cluster_embeddings(embeddings)
            semantic_entropy = self._calculate_cluster_entropy(clusters)
            semantic_clusters = len(set(clusters))
        else:
            # 简化版：基于句子长度分布的熵（无 embedding 时的近似）
            sentence_lengths = [len(s.split()) for s in sentences]
            length_counts = Counter(sentence_lengths)
            
            total = len(sentence_lengths)
            semantic_entropy = 0.0
            for count in length_counts.values():
                probability = count / total
                if probability > 0:
                    semantic_entropy -= probability * math.log2(probability)
            
            semantic_clusters = len(length_counts)
        
        # 3. 更新结果
        base_result = self.calculate_token_entropy(text)
        base_result.semantic_entropy = semantic_entropy
        base_result.semantic_clusters = semantic_clusters
        
        # 4. 重新评估健康度（考虑语义熵）
        if semantic_entropy is not None:
            # 语义熵越低，说明内容越聚焦
            semantic_factor = 1.0 - min(semantic_entropy / 5.0, 1.0)  # 归一化
            base_result.health_score = base_result.health_score * 0.5 + semantic_factor * 0.5
            base_result.health_level = self._health_level_from_score(base_result.health_score)
        
        logger.info(
            f"语义熵计算完成：semantic_entropy={semantic_entropy:.4f}, "
            f"clusters={semantic_clusters}, health={base_result.health_level}"
        )
        
        return base_result
    
    def compare_prompt_entropy(
        self, 
        before_text: str, 
        after_text: str
    ) -> Dict[str, Any]:
        """
        比较 Meditation 前后的提示词熵变化
        
        Args:
            before_text: Meditation 前的提示词
            after_text: Meditation 后的提示词
            
        Returns:
            包含熵变对比的字典
        """
        before_result = self.calculate_token_entropy(before_text)
        after_result = self.calculate_token_entropy(after_text)
        
        entropy_change = after_result.token_entropy - before_result.token_entropy
        entropy_change_percent = (
            (entropy_change / before_result.token_entropy * 100) 
            if before_result.token_entropy > 0 else 0
        )
        
        perplexity_change = after_result.token_perplexity - before_result.token_perplexity
        health_improvement = after_result.health_score - before_result.health_score
        
        return {
            "before": before_result.to_dict(),
            "after": after_result.to_dict(),
            "entropy_change": round(entropy_change, 4),
            "entropy_change_percent": round(entropy_change_percent, 2),
            "perplexity_change": round(perplexity_change, 4),
            "health_improvement": round(health_improvement, 4),
            "summary": self._generate_comparison_summary(
                entropy_change, perplexity_change, health_improvement
            )
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """
        简化版分词（按空格和标点分割）
        
        实际部署时可替换为更专业的分词器（如 jieba、spaCy 等）
        """
        import re
        # 移除标点，转小写，分割
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # 过滤掉太短的词
        tokens = [t for t in tokens if len(t) > 1]
        return tokens
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割文本为句子"""
        import re
        sentences = re.split(r'[.!?。！？]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _cluster_embeddings(self, embeddings: List[List[float]], n_clusters: int = 5) -> List[int]:
        """
        简单的 K-Means 聚类（简化版）
        
        实际部署时建议使用 sklearn 或更专业的聚类算法
        """
        # 简化实现：基于余弦相似度的贪心聚类
        if len(embeddings) == 0:
            return []
        
        clusters = []
        cluster_centers = []
        
        # 初始化：选择前 n_clusters 个作为初始中心
        k = min(n_clusters, len(embeddings))
        cluster_centers = embeddings[:k]
        
        for emb in embeddings:
            # 找到最近的聚类中心
            min_dist = float('inf')
            closest_cluster = 0
            
            for i, center in enumerate(cluster_centers):
                # 余弦距离
                dot = sum(a * b for a, b in zip(emb, center))
                norm_emb = math.sqrt(sum(a * a for a in emb))
                norm_center = math.sqrt(sum(a * a for a in center))
                if norm_emb > 0 and norm_center > 0:
                    cosine_sim = dot / (norm_emb * norm_center)
                    dist = 1 - cosine_sim
                    if dist < min_dist:
                        min_dist = dist
                        closest_cluster = i
            
            clusters.append(closest_cluster)
        
        return clusters
    
    def _calculate_cluster_entropy(self, clusters: List[int]) -> float:
        """计算簇分布的 Shannon 熵"""
        if len(clusters) == 0:
            return 0.0
        
        cluster_counts = Counter(clusters)
        total = len(clusters)
        
        entropy = 0.0
        for count in cluster_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _evaluate_health(
        self,
        entropy: float,
        information_density: float,
        unique_token_ratio: float,
        total_tokens: int
    ) -> Tuple[float, str, List[str]]:
        """
        评估提示词健康度
        
        Returns:
            (health_score, health_level, recommendations)
        """
        recommendations = []
        health_score = 0.0
        
        # 1. 基于信息密度评分（0.4-0.8 为佳）
        if 0.4 <= information_density <= 0.8:
            health_score += 0.4
        elif 0.3 <= information_density < 0.4 or 0.8 < information_density <= 0.9:
            health_score += 0.2
            if information_density > 0.8:
                recommendations.append("信息密度偏高，可能存在过多专业术语或复杂表达")
            else:
                recommendations.append("信息密度偏低，可能存在冗余内容")
        else:
            if information_density < 0.3:
                recommendations.append("信息密度过低，建议精简内容")
            else:
                recommendations.append("信息密度过高，可能影响理解")
        
        # 2. 基于唯一 token 比例评分
        if 0.5 <= unique_token_ratio <= 0.9:
            health_score += 0.3
        elif unique_token_ratio < 0.5:
            health_score += 0.1
            recommendations.append("重复内容较多，建议减少冗余")
        else:
            health_score += 0.2
            recommendations.append("词汇过于分散，可能缺乏焦点")
        
        # 3. 基于总 token 数评分
        if total_tokens < 100:
            health_score += 0.2
        elif total_tokens < 500:
            health_score += 0.15
        elif total_tokens < 2000:
            health_score += 0.1
            recommendations.append("提示词较长，考虑进一步压缩")
        else:
            recommendations.append("提示词过长，强烈建议压缩或分层注入")
        
        # 4. 基于熵值绝对值评分
        if entropy < 3.0:
            health_score += 0.1  # 低熵，内容聚焦
        elif entropy < 6.0:
            health_score += 0.05  # 中等熵
        else:
            recommendations.append("熵值较高，内容复杂度大")
        
        # 归一化到 0-1
        health_score = min(1.0, health_score)
        health_level = self._health_level_from_score(health_score)
        
        return health_score, health_level, recommendations
    
    def _health_level_from_score(self, score: float) -> str:
        """从分数转换为健康等级"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _generate_comparison_summary(
        self,
        entropy_change: float,
        perplexity_change: float,
        health_improvement: float
    ) -> str:
        """生成对比总结"""
        if entropy_change < -0.5:
            entropy_summary = "熵显著降低（信息更聚焦）"
        elif entropy_change < 0:
            entropy_summary = "熵略有降低"
        elif entropy_change < 0.5:
            entropy_summary = "熵基本持平"
        else:
            entropy_summary = "熵增加（信息更复杂）"
        
        if health_improvement > 0.1:
            health_summary = "健康度显著提升"
        elif health_improvement > 0:
            health_summary = "健康度略有改善"
        elif health_improvement > -0.1:
            health_summary = "健康度基本持平"
        else:
            health_summary = "健康度下降"
        
        return f"{entropy_summary}，{health_summary}"
