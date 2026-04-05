#!/usr/bin/env python3
"""
局部敏感哈希（LSH）：近似最近邻搜索
用于快速相似度搜索，特别适合大规模数据
"""

import numpy as np
import hashlib
from typing import List, Dict, Tuple, Set
import random

class LocalitySensitiveHashing:
    """局部敏感哈希：近似最近邻搜索"""
    
    def __init__(self, dimensions: int = 128, num_tables: int = 10, hash_size: int = 10):
        """
        初始化LSH
        
        Args:
            dimensions: 向量维度
            num_tables: 哈希表数量
            hash_size: 哈希值大小（位数）
        """
        self.dimensions = dimensions
        self.num_tables = num_tables
        self.hash_size = hash_size
        
        # 初始化哈希表
        self.hash_tables = [{} for _ in range(num_tables)]
        
        # 生成随机超平面（用于投影）
        self.random_planes = []
        for _ in range(num_tables * hash_size):
            plane = np.random.randn(dimensions)
            plane = plane / np.linalg.norm(plane)  # 归一化
            self.random_planes.append(plane)
        
        print(f"🔑 LSH初始化：维度={dimensions}, 哈希表={num_tables}, 哈希大小={hash_size}")
    
    def _compute_hash(self, vector: np.ndarray, table_idx: int) -> str:
        """计算向量的哈希值"""
        hash_bits = []
        
        for i in range(self.hash_size):
            plane_idx = table_idx * self.hash_size + i
            plane = self.random_planes[plane_idx]
            
            # 计算投影值
            projection = np.dot(vector, plane)
            
            # 二值化
            bit = 1 if projection >= 0 else 0
            hash_bits.append(str(bit))
        
        # 将二进制字符串转换为十六进制哈希
        binary_str = ''.join(hash_bits)
        hex_hash = hex(int(binary_str, 2))[2:].zfill((self.hash_size + 3) // 4)
        
        return hex_hash
    
    def add_vector(self, vector_id: str, vector: np.ndarray) -> None:
        """添加向量到LSH索引"""
        # 归一化向量
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        # 添加到所有哈希表
        for table_idx in range(self.num_tables):
            hash_value = self._compute_hash(vector, table_idx)
            
            if hash_value not in self.hash_tables[table_idx]:
                self.hash_tables[table_idx][hash_value] = []
            
            self.hash_tables[table_idx][hash_value].append((vector_id, vector))
    
    def query_similar(self, query_vector: np.ndarray, k: int = 10, 
                     threshold: float = 0.7, max_candidates: int = 100) -> List[Tuple[str, float]]:
        """查询相似向量"""
        # 归一化查询向量
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # 收集候选向量
        candidates = set()
        
        for table_idx in range(self.num_tables):
            hash_value = self._compute_hash(query_vector, table_idx)
            
            if hash_value in self.hash_tables[table_idx]:
                for vector_id, vector in self.hash_tables[table_idx][hash_value]:
                    candidates.add(vector_id)
            
            # 如果候选数量足够，提前停止
            if len(candidates) >= max_candidates:
                break
        
        # 计算相似度
        results = []
        for vector_id in candidates:
            # 需要从任意哈希表中获取向量
            vector = None
            for table in self.hash_tables:
                for hash_val, vectors in table.items():
                    for vid, vec in vectors:
                        if vid == vector_id:
                            vector = vec
                            break
                    if vector is not None:
                        break
                if vector is not None:
                    break
            
            if vector is not None:
                similarity = np.dot(query_vector, vector)
                if similarity >= threshold:
                    results.append((vector_id, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
    
    def batch_add_vectors(self, vectors: List[Tuple[str, np.ndarray]]) -> None:
        """批量添加向量"""
        print(f"📦 批量添加 {len(vectors)} 个向量")
        
        for vector_id, vector in vectors:
            self.add_vector(vector_id, vector)
        
        # 统计哈希表分布
        self._print_statistics()
    
    def _print_statistics(self) -> None:
        """打印统计信息"""
        total_entries = 0
        bucket_sizes = []
        
        for table in self.hash_tables:
            total_entries += sum(len(bucket) for bucket in table.values())
            bucket_sizes.extend(len(bucket) for bucket in table.values())
        
        if bucket_sizes:
            avg_bucket_size = np.mean(bucket_sizes)
            max_bucket_size = np.max(bucket_sizes)
            min_bucket_size = np.min(bucket_sizes)
            
            print(f"📊 LSH统计：")
            print(f"   总条目数：{total_entries}")
            print(f"   哈希桶数：{len(bucket_sizes)}")
            print(f"   平均桶大小：{avg_bucket_size:.1f}")
            print(f"   最大桶大小：{max_bucket_size}")
            print(f"   最小桶大小：{min_bucket_size}")
            print(f"   负载因子：{total_entries / (len(bucket_sizes) * self.num_tables):.2f}")
    
    def save_index(self, filepath: str) -> None:
        """保存LSH索引"""
        import pickle
        
        data = {
            'dimensions': self.dimensions,
            'num_tables': self.num_tables,
            'hash_size': self.hash_size,
            'random_planes': self.random_planes,
            'hash_tables': self.hash_tables
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✅ LSH索引已保存：{filepath}")
    
    def load_index(self, filepath: str) -> None:
        """加载LSH索引"""
        import pickle
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.dimensions = data['dimensions']
        self.num_tables = data['num_tables']
        self.hash_size = data['hash_size']
        self.random_planes = data['random_planes']
        self.hash_tables = data['hash_tables']
        
        print(f"✅ LSH索引已加载：{filepath}")
        self._print_statistics()

def test_lsh():
    """测试局部敏感哈希"""
    print("🧪 测试局部敏感哈希（LSH）")
    print("=" * 50)
    
    # 创建测试数据
    np.random.seed(42)
    num_points = 1000
    dimensions = 128
    
    vectors = []
    for i in range(num_points):
        vector_id = f"vec_{i:04d}"
        vector = np.random.randn(dimensions)
        vectors.append((vector_id, vector))
    
    print(f"📊 测试数据：{num_points} 个向量，{dimensions} 维")
    
    # 创建LSH索引
    lsh = LocalitySensitiveHashing(
        dimensions=dimensions,
        num_tables=5,
        hash_size=12
    )
    
    # 批量添加向量
    lsh.batch_add_vectors(vectors)
    
    # 测试查询
    query_vector = np.random.randn(dimensions)
    
    print(f"\n🔍 测试查询：")
    
    # LSH查询
    import time
    start_time = time.time()
    lsh_results = lsh.query_similar(query_vector, k=10, threshold=0.7)
    lsh_time = time.time() - start_time
    
    print(f"   LSH查询时间：{lsh_time:.4f} 秒")
    print(f"   找到 {len(lsh_results)} 个相似向量")
    
    # 暴力查询（对比）
    start_time = time.time()
    brute_results = []
    for vector_id, vector in vectors:
        norm = np.linalg.norm(vector)
        if norm > 0:
            normalized_vector = vector / norm
        else:
            normalized_vector = vector
        
        norm_query = np.linalg.norm(query_vector)
        if norm_query > 0:
            normalized_query = query_vector / norm_query
        else:
            normalized_query = query_vector
        
        similarity = np.dot(normalized_query, normalized_vector)
        if similarity >= 0.7:
            brute_results.append((vector_id, similarity))
    
    brute_results.sort(key=lambda x: x[1], reverse=True)
    brute_results = brute_results[:10]
    brute_time = time.time() - start_time
    
    print(f"   暴力查询时间：{brute_time:.4f} 秒")
    print(f"   加速比：{brute_time/lsh_time:.1f} 倍")
    
    # 验证结果质量
    lsh_ids = {pid for pid, _ in lsh_results}
    brute_ids = {pid for pid, _ in brute_results}
    
    intersection = lsh_ids.intersection(brute_ids)
    precision = len(intersection) / len(lsh_ids) if lsh_ids else 0
    recall = len(intersection) / len(brute_ids) if brute_ids else 0
    
    print(f"\n📊 结果质量：")
    print(f"   精确率：{precision:.2%} ({len(intersection)}/{len(lsh_ids)})")
    print(f"   召回率：{recall:.2%} ({len(intersection)}/{len(brute_ids)})")
    
    # 显示查询结果
    print(f"\n📋 LSH查询结果（前3个）：")
    for i, (vector_id, similarity) in enumerate(lsh_results[:3]):
        print(f"   {i+1}. {vector_id}: 相似度={similarity:.3f}")
    
    # 保存和加载测试
    print(f"\n💾 保存和加载测试：")
    test_file = '/Users/liugang/.openclaw/workspace/lsh_index_test.pkl'
    lsh.save_index(test_file)
    
    # 创建新的LSH实例并加载
    lsh2 = LocalitySensitiveHashing(dimensions=dimensions)
    lsh2.load_index(test_file)
    
    # 测试加载后的查询
    lsh2_results = lsh2.query_similar(query_vector, k=5, threshold=0.7)
    print(f"   加载后查询结果：{len(lsh2_results)} 个相似向量")
    
    return lsh, lsh_results

if __name__ == "__main__":
    lsh, results = test_lsh()
    print(f"\n✅ LSH测试完成")
