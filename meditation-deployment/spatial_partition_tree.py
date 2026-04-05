#!/usr/bin/env python3
"""
空间分区树算法：用于高效相似度计算
将高维向量空间划分为树状结构，减少计算复杂度
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import heapq

class SpatialPartitionTree:
    """空间分区树：高效相似度计算数据结构"""
    
    def __init__(self, dimensions: int = 128, max_depth: int = 10, leaf_size: int = 10):
        """
        初始化空间分区树
        
        Args:
            dimensions: 向量维度
            max_depth: 最大深度
            leaf_size: 叶子节点最大大小
        """
        self.dimensions = dimensions
        self.max_depth = max_depth
        self.leaf_size = leaf_size
        self.root = None
        self.node_count = 0
        
        print(f"🌳 空间分区树初始化：维度={dimensions}, 最大深度={max_depth}, 叶子大小={leaf_size}")
    
    class Node:
        """分区树节点"""
        def __init__(self, depth: int, bounds: Tuple[np.ndarray, np.ndarray]):
            self.depth = depth
            self.bounds = bounds  # (min_bounds, max_bounds)
            self.children = []  # 子节点列表
            self.points = []  # 叶子节点存储的点
            self.is_leaf = True
    
    def build_tree(self, points: List[Tuple[str, np.ndarray]]) -> None:
        """构建空间分区树"""
        if not points:
            return
        
        # 计算全局边界
        all_vectors = np.array([vec for _, vec in points])
        min_bounds = np.min(all_vectors, axis=0)
        max_bounds = np.max(all_vectors, axis=0)
        
        # 创建根节点
        self.root = self.Node(0, (min_bounds, max_bounds))
        self.node_count = 1
        
        # 递归构建树
        self._build_recursive(self.root, points, 0)
        
        print(f"✅ 空间分区树构建完成：{self.node_count} 个节点，{len(points)} 个点")
    
    def _build_recursive(self, node: Node, points: List[Tuple[str, np.ndarray]], depth: int) -> None:
        """递归构建树"""
        if depth >= self.max_depth or len(points) <= self.leaf_size:
            # 达到终止条件，创建叶子节点
            node.points = points
            node.is_leaf = True
            return
        
        # 选择分割维度（方差最大的维度）
        vectors = np.array([vec for _, vec in points])
        variances = np.var(vectors, axis=0)
        split_dim = np.argmax(variances)
        
        # 计算分割值（中位数）
        split_values = vectors[:, split_dim]
        split_value = np.median(split_values)
        
        # 分割点
        left_points = []
        right_points = []
        
        for point_id, vector in points:
            if vector[split_dim] < split_value:
                left_points.append((point_id, vector))
            else:
                right_points.append((point_id, vector))
        
        # 如果分割不平衡，创建叶子节点
        if len(left_points) == 0 or len(right_points) == 0:
            node.points = points
            node.is_leaf = True
            return
        
        # 更新边界并创建子节点
        min_bounds, max_bounds = node.bounds
        
        # 左子节点边界
        left_max_bounds = max_bounds.copy()
        left_max_bounds[split_dim] = split_value
        
        # 右子节点边界
        right_min_bounds = min_bounds.copy()
        right_min_bounds[split_dim] = split_value
        
        # 创建子节点
        left_node = self.Node(depth + 1, (min_bounds, left_max_bounds))
        right_node = self.Node(depth + 1, (right_min_bounds, max_bounds))
        
        node.children = [left_node, right_node]
        node.is_leaf = False
        self.node_count += 2
        
        # 递归构建
        self._build_recursive(left_node, left_points, depth + 1)
        self._build_recursive(right_node, right_points, depth + 1)
    
    def find_similar_points(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """查找相似点"""
        if self.root is None:
            return []
        
        # 使用优先队列存储结果
        results = []
        
        # 递归搜索
        self._search_recursive(self.root, query_vector, k, threshold, results)
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
    
    def _search_recursive(self, node: Node, query_vector: np.ndarray, k: int, 
                         threshold: float, results: List[Tuple[str, float]]) -> None:
        """递归搜索相似点"""
        if node.is_leaf:
            # 叶子节点，计算所有点的相似度
            for point_id, vector in node.points:
                similarity = self._cosine_similarity(query_vector, vector)
                if similarity >= threshold:
                    heapq.heappush(results, (similarity, point_id))
                    if len(results) > k:
                        heapq.heappop(results)
        else:
            # 内部节点，检查子节点边界
            for child in node.children:
                if self._should_search_child(child, query_vector, threshold):
                    self._search_recursive(child, query_vector, k, threshold, results)
    
    def _should_search_child(self, child: Node, query_vector: np.ndarray, threshold: float) -> bool:
        """判断是否应该搜索子节点"""
        min_bounds, max_bounds = child.bounds
        
        # 计算查询向量到子节点边界的最小可能角度
        # 使用边界框近似
        closest_point = np.clip(query_vector, min_bounds, max_bounds)
        max_similarity = self._cosine_similarity(query_vector, closest_point)
        
        return max_similarity >= threshold
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def get_tree_stats(self) -> Dict:
        """获取树统计信息"""
        if self.root is None:
            return {}
        
        leaf_count = 0
        max_depth = 0
        
        def _traverse(node: 'SpatialPartitionTree.Node', depth: int):
            nonlocal leaf_count, max_depth
            
            max_depth = max(max_depth, depth)
            
            if node.is_leaf:
                leaf_count += 1
            else:
                for child in node.children:
                    _traverse(child, depth + 1)
        
        _traverse(self.root, 0)
        
        return {
            'total_nodes': self.node_count,
            'leaf_nodes': leaf_count,
            'max_depth': max_depth,
            'average_depth': max_depth / 2,  # 近似值
            'branching_factor': 2  # 二叉树
        }

def test_spatial_partition_tree():
    """测试空间分区树"""
    print("🧪 测试空间分区树算法")
    print("=" * 50)
    
    # 创建测试数据
    np.random.seed(42)
    num_points = 100
    dimensions = 128
    
    points = []
    for i in range(num_points):
        point_id = f"point_{i:03d}"
        vector = np.random.randn(dimensions)
        vector = vector / np.linalg.norm(vector)  # 归一化
        points.append((point_id, vector))
    
    print(f"📊 测试数据：{num_points} 个点，{dimensions} 维")
    
    # 构建空间分区树
    tree = SpatialPartitionTree(dimensions=dimensions, max_depth=8, leaf_size=5)
    tree.build_tree(points)
    
    # 获取树统计信息
    stats = tree.get_tree_stats()
    print(f"\n📈 树统计信息：")
    print(f"   总节点数：{stats['total_nodes']}")
    print(f"   叶子节点数：{stats['leaf_nodes']}")
    print(f"   最大深度：{stats['max_depth']}")
    print(f"   平均深度：{stats['average_depth']:.1f}")
    print(f"   分支因子：{stats['branching_factor']}")
    
    # 测试查询
    query_vector = np.random.randn(dimensions)
    query_vector = query_vector / np.linalg.norm(query_vector)
    
    print(f"\n🔍 测试查询：")
    
    # 使用空间分区树查询
    start_time = time.time()
    similar_points_tree = tree.find_similar_points(query_vector, k=5, threshold=0.7)
    tree_time = time.time() - start_time
    
    # 暴力查询（对比）
    start_time = time.time()
    similar_points_brute = []
    for point_id, vector in points:
        similarity = tree._cosine_similarity(query_vector, vector)
        if similarity >= 0.7:
            similar_points_brute.append((point_id, similarity))
    
    similar_points_brute.sort(key=lambda x: x[1], reverse=True)
    similar_points_brute = similar_points_brute[:5]
    brute_time = time.time() - start_time
    
    print(f"   空间分区树查询时间：{tree_time:.4f} 秒")
    print(f"   暴力查询时间：{brute_time:.4f} 秒")
    print(f"   加速比：{brute_time/tree_time:.1f} 倍")
    
    # 验证结果一致性
    tree_ids = {pid for pid, _ in similar_points_tree}
    brute_ids = {pid for pid, _ in similar_points_brute}
    
    intersection = tree_ids.intersection(brute_ids)
    print(f"   结果一致性：{len(intersection)}/{len(tree_ids)} 个点相同")
    
    # 显示查询结果
    print(f"\n📋 相似点查询结果：")
    for i, (point_id, similarity) in enumerate(similar_points_tree[:3]):
        print(f"   {i+1}. {point_id}: 相似度={similarity:.3f}")
    
    return tree, similar_points_tree

if __name__ == "__main__":
    import time
    
    tree, results = test_spatial_partition_tree()
    print(f"\n✅ 空间分区树测试完成")
