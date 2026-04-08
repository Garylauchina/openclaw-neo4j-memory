"""
Information-Theoretic Framework for Meditation

Implements the entropy minimization framework from VISION.md Section 7.
Provides quantitative metrics for measuring meditation effectiveness.

Key concepts:
1. Graph entropy: Shannon entropy based on node degree distribution
2. Entropy reduction operations: redundancy elimination, noise filtering, structuring, distillation
3. Three Laws priority encoding: Law 1 (high fidelity), Law 2/3 (medium), others (discardable)
4. Measurable optimization: meditation algorithm can self-improve via entropy reduction metrics
"""

import math
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EntropyReductionCategory(Enum):
    """Four categories of entropy reduction operations from VISION.md"""
    REDUNDANCY_ELIMINATION = "redundancy_elimination"    # Lossless compression
    NOISE_FILTERING = "noise_filtering"                  # Lossy compression, improves SNR
    STRUCTURING = "structuring"                          # Same info, better organization
    DISTILLATION = "distillation"                        # Extreme compression


class ThreeLawsPriority(Enum):
    """Priority encoding based on Three Laws of Metacognition"""
    LAW_1_HIGH_FIDELITY = "law_1_high"      # User intent understanding (preserve at high fidelity)
    LAW_2_MEDIUM_FIDELITY = "law_2_medium"  # Self-reflection on performance
    LAW_3_MEDIUM_FIDELITY = "law_3_medium"  # Capability boundaries
    OTHER_DISCARDABLE = "other_discard"     # Can be aggressively compressed or discarded


class GraphEntropyMetrics:
    """Computes information-theoretic metrics for knowledge graphs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_node_degree_entropy(self, degree_counts: Dict[int, int], total_nodes: int) -> float:
        """Compute Shannon entropy of node degree distribution
        
        Args:
            degree_counts: dict mapping degree value to count
            total_nodes: total number of nodes in graph
            
        Returns:
            Entropy value in bits
        """
        if total_nodes == 0:
            return 0.0
        
        entropy = 0.0
        for degree, count in degree_counts.items():
            probability = count / total_nodes
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        self.logger.info(f"Node degree entropy: {entropy:.4f} bits (nodes: {total_nodes}, unique degrees: {len(degree_counts)})")
        return entropy
    
    def compute_relation_type_entropy(self, relation_counts: Dict[str, int], total_relations: int) -> float:
        """Compute Shannon entropy of relation type distribution"""
        if total_relations == 0:
            return 0.0
        
        entropy = 0.0
        for rel_type, count in relation_counts.items():
            probability = count / total_relations
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        self.logger.info(f"Relation type entropy: {entropy:.4f} bits (relations: {total_relations}, unique types: {len(relation_counts)})")
        return entropy
    
    def compute_confidence_entropy(self, confidence_counts: Dict[str, int], total_items: int) -> float:
        """Compute entropy of confidence score distribution (binned)"""
        if total_items == 0:
            return 0.0
        
        entropy = 0.0
        for bin_range, count in confidence_counts.items():
            probability = count / total_items
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        self.logger.info(f"Confidence entropy: {entropy:.4f} bits (items: {total_items}, bins: {len(confidence_counts)})")
        return entropy
    
    def compute_composite_graph_entropy(self, graph_stats: Dict[str, Any]) -> Dict[str, float]:
        """Compute composite entropy metrics for a knowledge graph
        
        Args:
            graph_stats: dictionary containing graph statistics
                - node_degree_counts: dict of degree->count
                - total_nodes: int
                - relation_type_counts: dict of relation_type->count
                - total_relations: int
                - confidence_bin_counts: dict of bin->count (e.g., "0.8-1.0"->count)
                - total_confidences: int
                
        Returns:
            Dictionary of entropy metrics
        """
        metrics = {}
        
        # Node degree entropy
        if 'node_degree_counts' in graph_stats and 'total_nodes' in graph_stats:
            metrics['node_degree_entropy'] = self.compute_node_degree_entropy(
                graph_stats['node_degree_counts'], 
                graph_stats['total_nodes']
            )
        
        # Relation type entropy
        if 'relation_type_counts' in graph_stats and 'total_relations' in graph_stats:
            metrics['relation_type_entropy'] = self.compute_relation_type_entropy(
                graph_stats['relation_type_counts'],
                graph_stats['total_relations']
            )
        
        # Confidence entropy
        if 'confidence_bin_counts' in graph_stats and 'total_confidences' in graph_stats:
            metrics['confidence_entropy'] = self.compute_confidence_entropy(
                graph_stats['confidence_bin_counts'],
                graph_stats['total_confidences']
            )
        
        # Composite entropy (weighted average)
        weights = {'node': 0.4, 'relation': 0.4, 'confidence': 0.2}
        total_weight = 0
        weighted_sum = 0
        
        if 'node_degree_entropy' in metrics:
            weighted_sum += metrics['node_degree_entropy'] * weights['node']
            total_weight += weights['node']
        
        if 'relation_type_entropy' in metrics:
            weighted_sum += metrics['relation_type_entropy'] * weights['relation']
            total_weight += weights['relation']
        
        if 'confidence_entropy' in metrics:
            weighted_sum += metrics['confidence_entropy'] * weights['confidence']
            total_weight += weights['confidence']
        
        if total_weight > 0:
            metrics['composite_entropy'] = weighted_sum / total_weight
            self.logger.info(f"Composite graph entropy: {metrics['composite_entropy']:.4f} bits")
        else:
            metrics['composite_entropy'] = 0.0
        
        return metrics


class EntropyReductionAnalyzer:
    """Analyzes entropy reduction across meditation operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def measure_redundancy_elimination(self, nodes_merged: int, nodes_total: int) -> Dict[str, Any]:
        """Measure entropy reduction from redundancy elimination (lossless compression)
        
        Args:
            nodes_merged: number of nodes merged
            nodes_total: total nodes considered for merging
            
        Returns:
            Dictionary with analysis metrics
        """
        if nodes_total == 0:
            return {"category": EntropyReductionCategory.REDUNDANCY_ELIMINATION.value,
                    "entropy_reduction": 0.0,
                    "compression_ratio": 1.0}
        
        compression_ratio = 1.0 - (nodes_merged / nodes_total) if nodes_total > 0 else 1.0
        # Theoretical entropy reduction for merging redundant nodes
        # Merging n redundant nodes reduces entropy by log2(n) bits per merge
        entropy_reduction = nodes_merged * math.log2(min(nodes_merged + 1, 10)) / max(nodes_total, 1)
        
        self.logger.info(f"Redundancy elimination: merged {nodes_merged}/{nodes_total} nodes, "
                        f"compression ratio: {compression_ratio:.3f}, "
                        f"entropy reduction: {entropy_reduction:.4f} bits")
        
        return {
            "category": EntropyReductionCategory.REDUNDANCY_ELIMINATION.value,
            "entropy_reduction": entropy_reduction,
            "compression_ratio": compression_ratio,
            "nodes_merged": nodes_merged,
            "nodes_total": nodes_total
        }
    
    def measure_noise_filtering(self, nodes_pruned: int, low_confidence_nodes: int) -> Dict[str, Any]:
        """Measure entropy reduction from noise filtering (lossy compression, improves SNR)
        
        Args:
            nodes_pruned: number of nodes removed
            low_confidence_nodes: total low-confidence nodes considered
            
        Returns:
            Dictionary with analysis metrics
        """
        if low_confidence_nodes == 0:
            return {"category": EntropyReductionCategory.NOISE_FILTERING.value,
                    "entropy_reduction": 0.0,
                    "snr_improvement": 1.0}
        
        removal_ratio = nodes_pruned / low_confidence_nodes
        # Removing noise improves signal-to-noise ratio
        # Maximum SNR improvement when all noise removed
        snr_improvement = 1.0 / (1.0 - removal_ratio) if removal_ratio < 1.0 else 10.0
        
        # Entropy reduction: noise typically has higher entropy than signal
        entropy_reduction = removal_ratio * math.log2(low_confidence_nodes + 1) / 10.0
        
        self.logger.info(f"Noise filtering: pruned {nodes_pruned}/{low_confidence_nodes} low-confidence nodes, "
                        f"SNR improvement: {snr_improvement:.2f}x, "
                        f"entropy reduction: {entropy_reduction:.4f} bits")
        
        return {
            "category": EntropyReductionCategory.NOISE_FILTERING.value,
            "entropy_reduction": entropy_reduction,
            "snr_improvement": snr_improvement,
            "nodes_pruned": nodes_pruned,
            "low_confidence_nodes": low_confidence_nodes
        }
    
    def measure_structuring(self, nodes_organized: int, hierarchy_levels_added: int) -> Dict[str, Any]:
        """Measure entropy reduction from structuring (better organization)
        
        Args:
            nodes_organized: number of nodes placed in hierarchy/causal structure
            hierarchy_levels_added: number of new hierarchical levels created
            
        Returns:
            Dictionary with analysis metrics
        """
        # Structural entropy reduction: better organization reduces search complexity
        # From O(n) to O(log n) retrieval complexity
        complexity_reduction = math.log2(max(nodes_organized, 2)) / max(nodes_organized, 1)
        
        entropy_reduction = (nodes_organized * hierarchy_levels_added * complexity_reduction) / 100.0
        
        self.logger.info(f"Structuring: organized {nodes_organized} nodes into {hierarchy_levels_added} levels, "
                        f"complexity reduction: {complexity_reduction:.4f}, "
                        f"entropy reduction: {entropy_reduction:.4f} bits")
        
        return {
            "category": EntropyReductionCategory.STRUCTURING.value,
            "entropy_reduction": entropy_reduction,
            "complexity_reduction": complexity_reduction,
            "nodes_organized": nodes_organized,
            "hierarchy_levels_added": hierarchy_levels_added
        }
    
    def measure_distillation(self, rules_extracted: int, events_considered: int) -> Dict[str, Any]:
        """Measure entropy reduction from distillation (extreme compression)
        
        Args:
            rules_extracted: number of general rules extracted
            events_considered: number of specific events considered
            
        Returns:
            Dictionary with analysis metrics
        """
        if events_considered == 0:
            return {"category": EntropyReductionCategory.DISTILLATION.value,
                    "entropy_reduction": 0.0,
                    "compression_factor": 1.0}
        
        compression_factor = events_considered / max(rules_extracted, 1)
        
        # Distillation: extracting general rules from specific events
        # Extreme compression: many events → few rules
        entropy_reduction = math.log2(compression_factor + 1) * rules_extracted / 10.0
        
        self.logger.info(f"Distillation: extracted {rules_extracted} rules from {events_considered} events, "
                        f"compression factor: {compression_factor:.1f}x, "
                        f"entropy_reduction: {entropy_reduction:.4f} bits")
        
        return {
            "category": EntropyReductionCategory.DISTILLATION.value,
            "entropy_reduction": entropy_reduction,
            "compression_factor": compression_factor,
            "rules_extracted": rules_extracted,
            "events_considered": events_considered
        }
    
    def analyze_meditation_run(self, meditation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entropy reduction for a complete meditation run
        
        Args:
            meditation_result: dictionary with meditation statistics
                Expected keys from meditation worker results
        
        Returns:
            Comprehensive entropy reduction analysis
        """
        analysis = {
            "entropy_reduction_operations": [],
            "total_entropy_reduction": 0.0,
            "category_breakdown": {},
            "three_laws_priority_encoding": {}
        }
        
        # 1. Analyze redundancy elimination (from entity merging)
        if 'entity_merge_count' in meditation_result and 'candidate_merge_count' in meditation_result:
            redundancy_analysis = self.measure_redundancy_elimination(
                meditation_result.get('entity_merge_count', 0),
                meditation_result.get('candidate_merge_count', 0)
            )
            analysis["entropy_reduction_operations"].append(redundancy_analysis)
            analysis["total_entropy_reduction"] += redundancy_analysis["entropy_reduction"]
            category = redundancy_analysis["category"]
            analysis["category_breakdown"][category] = analysis["category_breakdown"].get(category, 0) + redundancy_analysis["entropy_reduction"]
        
        # 2. Analyze noise filtering (from pruning)
        if 'nodes_pruned_by_connectivity' in meditation_result or 'nodes_pruned_by_weight' in meditation_result:
            nodes_pruned = (meditation_result.get('nodes_pruned_by_connectivity', 0) + 
                          meditation_result.get('nodes_pruned_by_weight', 0))
            low_conf_nodes = meditation_result.get('low_confidence_nodes', nodes_pruned * 2)
            
            noise_analysis = self.measure_noise_filtering(nodes_pruned, low_conf_nodes)
            analysis["entropy_reduction_operations"].append(noise_analysis)
            analysis["total_entropy_reduction"] += noise_analysis["entropy_reduction"]
            category = noise_analysis["category"]
            analysis["category_breakdown"][category] = analysis["category_breakdown"].get(category, 0) + noise_analysis["entropy_reduction"]
        
        # 3. Analyze structuring (from relation relabeling and hierarchical organization)
        if 'relation_relabeled_count' in meditation_result:
            nodes_organized = meditation_result.get('relation_relabeled_count', 0) * 2  # Approximate
            hierarchy_levels = meditation_result.get('hierarchical_relations_created', 0)
            
            structuring_analysis = self.measure_structuring(nodes_organized, hierarchy_levels)
            analysis["entropy_reduction_operations"].append(structuring_analysis)
            analysis["total_entropy_reduction"] += structuring_analysis["entropy_reduction"]
            category = structuring_analysis["category"]
            analysis["category_breakdown"][category] = analysis["category_breakdown"].get(category, 0) + structuring_analysis["entropy_reduction"]
        
        # 4. Analyze distillation (from knowledge distillation)
        if 'meta_knowledge_created' in meditation_result:
            rules_extracted = meditation_result.get('meta_knowledge_created', 0)
            # Assume each meta-knowledge node distills many events
            events_considered = rules_extracted * 10  # Conservative estimate
            
            distillation_analysis = self.measure_distillation(rules_extracted, events_considered)
            analysis["entropy_reduction_operations"].append(distillation_analysis)
            analysis["total_entropy_reduction"] += distillation_analysis["entropy_reduction"]
            category = distillation_analysis["category"]
            analysis["category_breakdown"][category] = analysis["category_breakdown"].get(category, 0) + distillation_analysis["entropy_reduction"]
        
        # 5. Apply Three Laws priority encoding
        analysis["three_laws_priority_encoding"] = self.apply_three_laws_priority(meditation_result)
        
        self.logger.info(f"Meditation entropy analysis complete: "
                        f"total reduction: {analysis['total_entropy_reduction']:.4f} bits, "
                        f"categories: {list(analysis['category_breakdown'].keys())}")
        
        return analysis
    
    def apply_three_laws_priority(self, meditation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Three Laws priority encoding to meditation results
        
        In information theory, prior knowledge improves compression efficiency.
        Three Laws tell the meditation algorithm what information matters most.
        """
        priority_encoding = {
            "law_1_high_fidelity": {
                "description": "User intent understanding (preserve at high fidelity)",
                "estimated_entropy_cost": 0.1,  # Low entropy cost, high importance
                "compression_ratio": 1.0  # No compression, preserve fully
            },
            "law_2_medium_fidelity": {
                "description": "Self-reflection on performance",
                "estimated_entropy_cost": 0.3,
                "compression_ratio": 0.7  # Moderate compression
            },
            "law_3_medium_fidelity": {
                "description": "Capability boundaries",
                "estimated_entropy_cost": 0.3,
                "compression_ratio": 0.7
            },
            "other_discardable": {
                "description": "Can be aggressively compressed or discarded",
                "estimated_entropy_cost": 0.8,
                "compression_ratio": 0.3  # High compression
            }
        }
        
        # Estimate distribution based on metacognition if available
        if 'metacognition_law1_insights' in meditation_result:
            total_insights = (meditation_result.get('metacognition_law1_insights', 0) +
                            meditation_result.get('metacognition_law2_insights', 0) +
                            meditation_result.get('metacognition_law3_insights', 0))
            
            if total_insights > 0:
                priority_encoding["law_1_high_fidelity"]["percentage"] = (
                    meditation_result.get('metacognition_law1_insights', 0) / total_insights * 100)
                priority_encoding["law_2_medium_fidelity"]["percentage"] = (
                    meditation_result.get('metacognition_law2_insights', 0) / total_insights * 100)
                priority_encoding["law_3_medium_fidelity"]["percentage"] = (
                    meditation_result.get('metacognition_law3_insights', 0) / total_insights * 100)
        
        return priority_encoding


class MeditationOptimizer:
    """Self-optimizing meditation algorithm based on entropy minimization"""
    
    def __init__(self):
        self.entropy_calculator = GraphEntropyMetrics()
        self.entropy_analyzer = EntropyReductionAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Track performance over time
        self.history = []  # List of (strategy, entropy_reduction) tuples
        self.strategy_performance = {}  # strategy -> (total_reduction, count)
    
    def learn_optimal_strategy(self, graph_state: Dict[str, Any], 
                              available_strategies: List[str]) -> str:
        """Learn which meditation strategy works best for given graph state
        
        Args:
            graph_state: current graph metrics
            available_strategies: list of strategy names
            
        Returns:
            Best strategy based on historical performance
        """
        if not self.history:
            # No history yet, return default strategy
            return available_strategies[0] if available_strategies else "default"
        
        # Simple heuristic: choose strategy with highest average entropy reduction
        best_strategy = available_strategies[0]
        best_avg_reduction = 0.0
        
        for strategy in available_strategies:
            if strategy in self.strategy_performance:
                total_reduction, count = self.strategy_performance[strategy]
                avg_reduction = total_reduction / count
                if avg_reduction > best_avg_reduction:
                    best_avg_reduction = avg_reduction
                    best_strategy = strategy
        
        self.logger.info(f"Selected strategy '{best_strategy}' with avg entropy reduction: {best_avg_reduction:.4f}")
        return best_strategy
    
    def update_strategy_performance(self, strategy: str, entropy_reduction: float):
        """Update performance tracking for a strategy"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = (0.0, 0)
        
        total_reduction, count = self.strategy_performance[strategy]
        total_reduction += entropy_reduction
        count += 1
        self.strategy_performance[strategy] = (total_reduction, count)
        
        self.history.append((strategy, entropy_reduction))
        
        # Keep history manageable
        if len(self.history) > 100:
            self.history = self.history[-50:]
        
        self.logger.info(f"Updated strategy '{strategy}' performance: "
                        f"total reduction: {total_reduction:.4f}, count: {count}, "
                        f"average: {total_reduction/count:.4f}")
    
    def optimize_meditation_parameters(self, current_metrics: Dict[str, float],
                                     historical_performance: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize meditation parameters based on historical performance
        
        This is Law 2 (reflect on performance) applied to the meditation algorithm itself.
        """
        optimization = {
            "recommended_parameters": {},
            "confidence": 0.5,
            "reasoning": "Default parameters"
        }
        
        # Simple optimization logic (can be enhanced with ML)
        if historical_performance:
            # Analyze what worked well in similar graph states
            similar_states = [p for p in historical_performance 
                            if abs(p.get('composite_entropy', 0) - current_metrics.get('composite_entropy', 0)) < 0.1]
            
            if similar_states:
                # Find parameters that gave highest entropy reduction in similar states
                best_performance = max(similar_states, key=lambda x: x.get('entropy_reduction', 0))
                optimization["recommended_parameters"] = best_performance.get('parameters', {})
                optimization["confidence"] = 0.7
                optimization["reasoning"] = f"Based on {len(similar_states)} similar historical states"
            else:
                # Use parameters that worked well overall
                overall_best = max(historical_performance, key=lambda x: x.get('entropy_reduction', 0))
                optimization["recommended_parameters"] = overall_best.get('parameters', {})
                optimization["confidence"] = 0.6
                optimization["reasoning"] = "Based on overall best performance"
        
        self.logger.info(f"Meditation parameter optimization: {optimization['reasoning']}, "
                        f"confidence: {optimization['confidence']:.2f}")
        return optimization


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("=== Information Theory Framework Test ===")
    
    # Create calculator
    calculator = GraphEntropyMetrics()
    
    # Example graph statistics
    graph_stats = {
        'node_degree_counts': {1: 100, 2: 50, 3: 25, 4: 10, 5: 5},
        'total_nodes': 190,
        'relation_type_counts': {'related_to': 200, 'causes': 50, 'part_of': 30, 'uses': 20},
        'total_relations': 300,
        'confidence_bin_counts': {'0.0-0.2': 10, '0.2-0.4': 20, '0.4-0.6': 40, '0.6-0.8': 60, '0.8-1.0': 60},
        'total_confidences': 190
    }
    
    # Compute entropy metrics
    metrics = calculator.compute_composite_graph_entropy(graph_stats)
    print(f"Composite graph entropy: {metrics.get('composite_entropy', 0):.4f} bits")
    
    # Create analyzer
    analyzer = EntropyReductionAnalyzer()
    
    # Example meditation results
    meditation_result = {
        'entity_merge_count': 12,
        'candidate_merge_count': 30,
        'nodes_pruned_by_connectivity': 8,
        'nodes_pruned_by_weight': 5,
        'low_confidence_nodes': 25,
        'relation_relabeled_count': 18,
        'hierarchical_relations_created': 6,
        'meta_knowledge_created': 4,
        'metacognition_law1_insights': 2,
        'metacognition_law2_insights': 1,
        'metacognition_law3_insights': 1
    }
    
    # Analyze entropy reduction
    analysis = analyzer.analyze_meditation_run(meditation_result)
    print(f"Total entropy reduction: {analysis['total_entropy_reduction']:.4f} bits")
    
    # Test optimizer
    optimizer = MeditationOptimizer()
    optimizer.update_strategy_performance("rule_based", 0.15)
    optimizer.update_strategy_performance("llm_assisted", 0.25)
    optimizer.update_strategy_performance("rule_based", 0.18)
    
    best_strategy = optimizer.learn_optimal_strategy(
        graph_state={'composite_entropy': 5.2},
        available_strategies=["rule_based", "llm_assisted", "hybrid"]
    )
    print(f"Best strategy for graph state: {best_strategy}")
    
    print("\n✅ Information theory framework is ready for integration with meditation pipeline!")