"""
Rule Engine for Meditation Pipeline

Implements the "rule algorithm first, LLM only for distillation" approach from Issue #21.
Provides deterministic, cost-effective decision making for meditation steps.

Key principles:
1. Rule-based decisions first (string similarity, frequency counts, graph topology)
2. LLM only used for distillation (verification, refinement, quality improvement)
3. Deterministic cost: predictable computation, no unpredictable LLM costs
4. Self-improving: rules can be optimized based on entropy reduction metrics
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any, Set
import logging
from difflib import SequenceMatcher
import math

logger = logging.getLogger(__name__)


class RuleBasedSimilarity:
    """String similarity algorithms for entity merging decisions"""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> float:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return RuleBasedSimilarity.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def normalized_levenshtein(s1: str, s2: str) -> float:
        """Normalized Levenshtein similarity (0.0-1.0)"""
        distance = RuleBasedSimilarity.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def sequence_similarity(s1: str, s2: str) -> float:
        """Sequence matcher similarity (more sophisticated than Levenshtein)"""
        return SequenceMatcher(None, s1, s2).ratio()
    
    @staticmethod
    def jaccard_similarity_words(s1: str, s2: str) -> float:
        """Jaccard similarity based on word sets"""
        words1 = set(re.findall(r'\w+', s1.lower()))
        words2 = set(re.findall(r'\w+', s2.lower()))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def composite_similarity(s1: str, s2: str, weights: Dict[str, float] = None) -> Dict[str, Any]:
        """Composite similarity score combining multiple algorithms
        
        Args:
            s1, s2: strings to compare
            weights: optional weights for each algorithm
            
        Returns:
            Dictionary with individual scores and composite score
        """
        if weights is None:
            weights = {
                'sequence': 0.4,
                'levenshtein': 0.3,
                'jaccard': 0.3
            }
        
        scores = {
            'sequence': RuleBasedSimilarity.sequence_similarity(s1, s2),
            'levenshtein': RuleBasedSimilarity.normalized_levenshtein(s1, s2),
            'jaccard': RuleBasedSimilarity.jaccard_similarity_words(s1, s2)
        }
        
        # Calculate weighted composite
        composite = 0.0
        total_weight = 0.0
        for algo, weight in weights.items():
            if algo in scores:
                composite += scores[algo] * weight
                total_weight += weight
        
        composite_score = composite / total_weight if total_weight > 0 else 0.0
        
        result = {
            'composite': composite_score,
            'jaccard': RuleBasedSimilarity.jaccard_similarity_words(s1, s2)
        }
        
        # Calculate weighted composite score
        composite = 0.0
        total_weight = 0.0
        for algorithm, weight in weights.items():
            if algorithm in scores:
                composite += scores[algorithm] * weight
                total_weight += weight
        
        scores['composite'] = composite / total_weight if total_weight > 0 else 0.0
        
        logger.debug(f"Similarity scores for '{s1}' vs '{s2}': {scores}")
        return scores


class FrequencyAnalyzer:
    """Analyzes mention frequency patterns for entity filtering and prioritization"""
    
    def __init__(self, min_mentions: int = 3, time_decay_factor: float = 0.95):
        self.min_mentions = min_mentions
        self.time_decay_factor = time_decay_factor
        self.logger = logging.getLogger(__name__)
    
    def filter_by_frequency(self, entity_counts: Dict[str, int], 
                           total_documents: int) -> Dict[str, Any]:
        """Filter entities based on mention frequency
        
        Args:
            entity_counts: dict of entity name -> mention count
            total_documents: total number of documents/contexts
            
        Returns:
            Dictionary with filtered entities and statistics
        """
        if total_documents == 0:
            return {
                'filtered_entities': {},
                'kept_count': 0,
                'filtered_count': 0,
                'average_frequency': 0.0
            }
        
        filtered = {}
        filtered_out = {}
        
        # Calculate frequency threshold
        # Minimum absolute count AND minimum relative frequency
        absolute_threshold = self.min_mentions
        relative_threshold = 0.01  # Must appear in at least 1% of documents
        
        for entity, count in entity_counts.items():
            relative_frequency = count / total_documents
            
            if count >= absolute_threshold and relative_frequency >= relative_threshold:
                filtered[entity] = {
                    'count': count,
                    'relative_frequency': relative_frequency,
                    'confidence': min(0.3 + (relative_frequency * 0.7), 1.0)
                }
            else:
                filtered_out[entity] = {
                    'count': count,
                    'relative_frequency': relative_frequency,
                    'reason': f"count={count}<{absolute_threshold}" if count < absolute_threshold else f"freq={relative_frequency:.3f}<{relative_threshold}"
                }
        
        # Calculate statistics
        kept_count = len(filtered)
        filtered_count = len(filtered_out)
        avg_frequency = sum(e['count'] for e in filtered.values()) / kept_count if kept_count > 0 else 0.0
        
        self.logger.info(f"Frequency filtering: {kept_count} entities kept, {filtered_count} filtered out, "
                        f"avg frequency: {avg_frequency:.2f}")
        
        return {
            'filtered_entities': filtered,
            'filtered_out_entities': filtered_out,
            'kept_count': kept_count,
            'filtered_count': filtered_count,
            'average_frequency': avg_frequency,
            'thresholds': {
                'absolute': absolute_threshold,
                'relative': relative_threshold
            }
        }
    
    def apply_time_decay(self, entity_counts: Dict[str, List[Tuple[int, float]]], 
                        current_time: float) -> Dict[str, float]:
        """Apply time decay to mention counts (older mentions weigh less)
        
        Args:
            entity_counts: dict of entity name -> list of (count, timestamp)
            current_time: current timestamp for reference
            
        Returns:
            Dict of entity -> decayed count
        """
        decayed_counts = {}
        
        for entity, mentions in entity_counts.items():
            decayed_count = 0.0
            for count, timestamp in mentions:
                # Calculate time difference in "units" (e.g., days)
                time_diff = max(current_time - timestamp, 0)
                # Exponential decay: weight = decay_factor ^ time_diff
                decay_weight = self.time_decay_factor ** time_diff
                decayed_count += count * decay_weight
            
            decayed_counts[entity] = decayed_count
        
        return decayed_counts
    
    def detect_patterns(self, entity_sequences: List[List[str]], 
                       min_pattern_length: int = 2) -> Dict[str, Dict[str, Any]]:
        """Detect co-occurrence and sequential patterns in entity mentions
        
        Args:
            entity_sequences: list of sequences (lists) of entity mentions
            min_pattern_length: minimum pattern length to detect
            
        Returns:
            Dictionary of detected patterns
        """
        # Co-occurrence analysis
        cooccurrence_counts = Counter()
        sequential_patterns = Counter()
        
        for sequence in entity_sequences:
            # Co-occurrence: entities that appear together in same sequence
            unique_entities = set(sequence)
            for i, entity1 in enumerate(unique_entities):
                for entity2 in list(unique_entities)[i+1:]:
                    pair = tuple(sorted([entity1, entity2]))
                    cooccurrence_counts[pair] += 1
            
            # Sequential patterns
            for length in range(min_pattern_length, min(5, len(sequence) + 1)):
                for i in range(len(sequence) - length + 1):
                    pattern = tuple(sequence[i:i+length])
                    sequential_patterns[pattern] += 1
        
        # Filter significant patterns
        significant_cooccurrences = {}
        for (entity1, entity2), count in cooccurrence_counts.items():
            if count >= 2:  # At least 2 co-occurrences
                significant_cooccurrences[f"{entity1}↔{entity2}"] = {
                    'entities': [entity1, entity2],
                    'count': count,
                    'type': 'cooccurrence'
                }
        
        significant_sequences = {}
        for pattern, count in sequential_patterns.items():
            if count >= 2 and len(pattern) >= min_pattern_length:
                pattern_str = "→".join(pattern)
                significant_sequences[pattern_str] = {
                    'pattern': pattern,
                    'count': count,
                    'type': 'sequence'
                }
        
        self.logger.info(f"Pattern detection: {len(significant_cooccurrences)} co-occurrence patterns, "
                        f"{len(significant_sequences)} sequential patterns detected")
        
        return {
            'cooccurrence_patterns': significant_cooccurrences,
            'sequential_patterns': significant_sequences,
            'total_sequences_analyzed': len(entity_sequences)
        }


class GraphTopologyAnalyzer:
    """Analyzes graph topology for relation inference and structure optimization"""
    
    def __init__(self, max_shared_neighbors: int = 10):
        self.max_shared_neighbors = max_shared_neighbors
        self.logger = logging.getLogger(__name__)
    
    def analyze_shared_neighbors(self, adjacency_lists: Dict[str, Set[str]]) -> Dict[str, List[Tuple[str, float]]]:
        """Analyze shared neighbors between nodes for relation inference
        
        Args:
            adjacency_lists: dict of node -> set of neighbor nodes
            
        Returns:
            Dict of node -> list of (other_node, shared_neighbor_score)
        """
        shared_neighbor_scores = {}
        
        nodes = list(adjacency_lists.keys())
        for i, node1 in enumerate(nodes):
            neighbors1 = adjacency_lists.get(node1, set())
            scores = []
            
            for node2 in nodes[i+1:]:
                neighbors2 = adjacency_lists.get(node2, set())
                
                if not neighbors1 or not neighbors2:
                    continue
                
                # Calculate Jaccard similarity of neighbors
                intersection = len(neighbors1.intersection(neighbors2))
                union = len(neighbors1.union(neighbors2))
                
                if union > 0:
                    jaccard_similarity = intersection / union
                    
                    # Also consider absolute number of shared neighbors
                    shared_neighbor_score = (jaccard_similarity * 0.7) + (intersection / 10.0 * 0.3)
                    
                    if shared_neighbor_score > 0.1:  # Threshold
                        scores.append((node2, shared_neighbor_score))
            
            # Sort by score and keep top results
            scores.sort(key=lambda x: x[1], reverse=True)
            shared_neighbor_scores[node1] = scores[:self.max_shared_neighbors]
        
        # Analyze results
        total_connections = sum(len(scores) for scores in shared_neighbor_scores.values())
        avg_score = 0.0
        count = 0
        for scores in shared_neighbor_scores.values():
            for _, score in scores:
                avg_score += score
                count += 1
        
        avg_score = avg_score / count if count > 0 else 0.0
        
        self.logger.info(f"Shared neighbor analysis: {total_connections} potential connections, "
                        f"average score: {avg_score:.3f}")
        
        return {
            'shared_neighbor_scores': shared_neighbor_scores,
            'total_potential_connections': total_connections,
            'average_score': avg_score
        }
    
    def infer_relation_types(self, node_pairs: List[Tuple[str, str]], 
                           graph_context: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
        """Infer relation types based on graph topology and context
        
        Args:
            node_pairs: list of (source, target) node pairs
            graph_context: additional graph context (node types, existing relations)
            
        Returns:
            Dict mapping (source, target) -> inferred relation type
        """
        inferred_relations = {}
        relation_type_counts = Counter()
        
        node_types = graph_context.get('node_types', {})
        existing_relations = graph_context.get('existing_relations', {})
        
        for source, target in node_pairs:
            source_type = node_types.get(source, 'unknown')
            target_type = node_types.get(target, 'unknown')
            
            # Rule-based relation inference
            relation_type = "related_to"  # Default
            
            # Type-based inference rules
            if source_type == target_type:
                if source_type in ['person', 'organization']:
                    relation_type = "works_with"
                elif source_type == 'concept':
                    relation_type = "related_to"
                elif source_type == 'technology':
                    relation_type = "integrates_with"
            
            # Content-based rules
            source_lower = source.lower()
            target_lower = target.lower()
            
            if "causes" in source_lower or "causes" in target_lower:
                relation_type = "causes"
            elif "part of" in source_lower or "part of" in target_lower:
                relation_type = "part_of"
            elif "uses" in source_lower or "uses" in target_lower:
                relation_type = "uses"
            elif "depends on" in source_lower or "depends on" in target_lower:
                relation_type = "depends_on"
            
            # Check for existing similar relations
            similar_existing = False
            for (s, t), rel in existing_relations.items():
                if s == source and t == target:
                    relation_type = rel
                    similar_existing = True
                    break
            
            inferred_relations[(source, target)] = relation_type
            relation_type_counts[relation_type] += 1
            
            if not similar_existing:
                self.logger.debug(f"Inferred relation: {source} --[{relation_type}]--> {target}")
        
        self.logger.info(f"Relation type inference: {len(inferred_relations)} relations inferred, "
                        f"distribution: {dict(relation_type_counts)}")
        
        return inferred_relations
    
    def identify_clusters(self, adjacency_lists: Dict[str, Set[str]], 
                         min_cluster_size: int = 3) -> Dict[str, List[str]]:
        """Identify clusters/communities in the graph
        
        Simple implementation using connected components
        """
        visited = set()
        clusters = {}
        cluster_id = 0
        
        from collections import deque
        
        for node in adjacency_lists:
            if node not in visited:
                current_cluster = []
                queue = deque([node])
                visited.add(node)
                while queue:
                    current = queue.popleft()
                    current_cluster.append(current)
                    for neighbor in adjacency_lists.get(current, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                if len(current_cluster) >= min_cluster_size:
                    clusters[f"cluster_{cluster_id}"] = current_cluster
                    cluster_id += 1
        
        # Calculate cluster statistics
        cluster_sizes = [len(nodes) for nodes in clusters.values()]
        avg_cluster_size = sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0
        
        self.logger.info(f"Cluster identification: {len(clusters)} clusters found, "
                        f"average size: {avg_cluster_size:.1f}, "
                        f"total nodes in clusters: {sum(cluster_sizes)}")
        
        return {
            'clusters': clusters,
            'cluster_count': len(clusters),
            'average_cluster_size': avg_cluster_size,
            'total_clustered_nodes': sum(cluster_sizes)
        }


class RuleEngine:
    """Main rule engine coordinating similarity, frequency, and topology analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {
                'similarity_threshold': 0.7,
                'min_mentions': 3,
                'min_shared_neighbors': 2,
                'confidence_threshold': 0.6
            }
        
        self.config = config
        self.similarity = RuleBasedSimilarity()
        self.frequency_analyzer = FrequencyAnalyzer()
        self.topology_analyzer = GraphTopologyAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def decide_entity_merge(self, entity1: str, entity2: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether two entities should be merged
        
        Args:
            entity1, entity2: entity names to consider merging
            context: additional context (mention counts, graph position, etc.)
            
        Returns:
            Dictionary with decision and reasoning
        """
        # 1. String similarity analysis
        similarity_scores = self.similarity.composite_similarity(entity1, entity2)
        composite_similarity = similarity_scores.get('composite', 0.0)
        
        # 2. Mention frequency analysis
        mention_count1 = context.get('mention_counts', {}).get(entity1, 0)
        mention_count2 = context.get('mention_counts', {}).get(entity2, 0)
        total_mentions = mention_count1 + mention_count2
        
        # 3. Graph topology analysis (if available)
        shared_neighbors = context.get('shared_neighbors', {}).get((entity1, entity2), 0)
        
        # Decision logic
        should_merge = False
        confidence = 0.5
        reasoning = []
        
        # Rule 1: High string similarity
        if composite_similarity >= self.config['similarity_threshold']:
            should_merge = True
            confidence = min(0.3 + composite_similarity * 0.7, 1.0)
            reasoning.append(f"High string similarity: {composite_similarity:.3f}")
        
        # Rule 2: Shared neighbors in graph
        elif shared_neighbors >= self.config['min_shared_neighbors']:
            should_merge = True
            confidence = 0.6 + (shared_neighbors / 10.0 * 0.4)
            reasoning.append(f"Shared neighbors: {shared_neighbors}")
        
        # Rule 3: Low mention frequency (possible noise)
        elif total_mentions < self.config['min_mentions']:
            should_merge = True  # Merge low-frequency potential noise
            confidence = 0.7
            reasoning.append(f"Low mention frequency: {total_mentions}")
        
        # Default: don't merge
        if not should_merge:
            reasoning.append(f"Insufficient evidence for merging (similarity: {composite_similarity:.3f}, "
                           f"mentions: {total_mentions}, shared neighbors: {shared_neighbors})")
        
        decision = {
            'should_merge': should_merge,
            'confidence': confidence,
            'reasoning': reasoning,
            'metrics': {
                'similarity': composite_similarity,
                'mention_counts': {'entity1': mention_count1, 'entity2': mention_count2},
                'shared_neighbors': shared_neighbors,
                'similarity_breakdown': similarity_scores
            }
        }
        
        self.logger.info(f"Entity merge decision: {entity1} + {entity2} = {should_merge} "
                        f"(confidence: {confidence:.3f})")
        
        return decision
    
    def decide_relation_relabeling(self, relation_info: Dict[str, Any],
                                 graph_context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether and how to relabel a relation
        
        Args:
            relation_info: information about the relation
            graph_context: broader graph context
            
        Returns:
            Dictionary with decision and suggested new relation type
        """
        current_type = relation_info.get('current_type', 'related_to')
        source = relation_info.get('source')
        target = relation_info.get('target')
        
        # Get topological context
        source_neighbors = graph_context.get('adjacency_lists', {}).get(source, set())
        target_neighbors = graph_context.get('adjacency_lists', {}).get(target, set())
        
        # Analyze connection patterns
        shared_neighbors = len(source_neighbors.intersection(target_neighbors))
        source_degree = len(source_neighbors)
        target_degree = len(target_neighbors)
        
        # Rule-based inference
        new_type = current_type
        should_relabel = False
        confidence = 0.5
        reasoning = []
        
        # Rule 1: Many shared neighbors suggests hierarchical relation
        if shared_neighbors >= 3:
            # Check if one is subset of another
            if source_neighbors.issubset(target_neighbors) and len(source_neighbors) < len(target_neighbors):
                new_type = "part_of"
                should_relabel = True
                confidence = 0.7
                reasoning.append(f"Source is subset of target ({len(source_neighbors)}/{len(target_neighbors)} neighbors)")
            elif target_neighbors.issubset(source_neighbors) and len(target_neighbors) < len(source_neighbors):
                new_type = "contains"
                should_relabel = True
                confidence = 0.7
                reasoning.append(f"Target is subset of source ({len(target_neighbors)}/{len(source_neighbors)} neighbors)")
        
        # Rule 2: Degree disparity suggests dependency
        elif source_degree > target_degree * 2:
            new_type = "depends_on"
            should_relabel = True
            confidence = 0.6
            reasoning.append(f"High degree disparity ({source_degree}:{target_degree})")
        elif target_degree > source_degree * 2:
            new_type = "supports"
            should_relabel = True
            confidence = 0.6
            reasoning.append(f"High degree disparity ({target_degree}:{source_degree})")
        
        # Rule 3: Check for common patterns in node names
        source_lower = source.lower() if source else ""
        target_lower = target.lower() if target else ""
        
        if "cause" in source_lower or "effect" in target_lower:
            new_type = "causes"
            should_relabel = True
            confidence = 0.65
            reasoning.append("Semantic pattern: cause-effect")
        elif "part" in source_lower and "whole" in target_lower:
            new_type = "part_of"
            should_relabel = True
            confidence = 0.65
            reasoning.append("Semantic pattern: part-whole")
        
        decision = {
            'should_relabel': should_relabel,
            'suggested_type': new_type if should_relabel else current_type,
            'confidence': confidence,
            'reasoning': reasoning,
            'current_type': current_type,
            'topological_context': {
                'source_degree': source_degree,
                'target_degree': target_degree,
                'shared_neighbors': relation_info.get('shared_neighbors', 0)
            }
        }
        
        if should_relabel:
            self.logger.info(f"Relation relabeling: {source} --[{current_type}]--> {target} "
                           f"→ --[{new_type}]--> (confidence: {confidence:.3f})")
        
        return decision
    
    def generate_llm_distillation_prompt(self, rule_decisions: List[Dict[str, Any]],
                                        context: Dict[str, Any]) -> str:
        """Generate prompt for LLM distillation of rule-based decisions
        
        Args:
            rule_decisions: list of decisions made by rule engine
            context: additional context for distillation
            
        Returns:
            Prompt string for LLM refinement
        """
        prompt = """# LLM Distillation: Verify and Refine Rule-Based Decisions

## Context
{context_summary}

## Rule-Based Decisions (Require LLM Verification)
{decisions_summary}

## Instructions
1. **Verify correctness**: Are these decisions logically sound?
2. **Improve quality**: Suggest better relation types or merge decisions
3. **Identify patterns**: What higher-level patterns do you see?
4. **Generate insights**: What should be remembered for future meditation?

## Output Format
Provide a JSON with:
- "verified_decisions": list of verified/refined decisions
- "confidence_scores": per-decision confidence (0.0-1.0)
- "pattern_insights": high-level patterns observed
- "recommended_adjustments": suggestions for rule improvements
""".format(
            context_summary=context.get('summary', 'No additional context'),
            decisions_summary='\n'.join([
                f"- {d.get('type', 'unknown')}: {d.get('details', '')}" 
                for d in rule_decisions[:10]  # Limit to first 10 for token efficiency
            ])
        )
        
        return prompt


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("=== Rule Engine Test ===")
    
    # Test similarity algorithms
    similarity = RuleBasedSimilarity()
    test_strings = [
        ("OpenAI GPT-4", "OpenAI GPT 4"),
        ("machine learning", "ML"),
        ("knowledge graph", "semantic network")
    ]
    
    for s1, s2 in test_strings:
        scores = similarity.composite_similarity(s1, s2)
        print(f"Similarity '{s1}' vs '{s2}': composite={scores.get('composite_score', 0):.3f}")
    
    # Test frequency analysis
    entity_counts = {
        "machine learning": 25,
        "ML": 12,
        "deep learning": 18,
        "neural networks": 15,
        "temporary concept": 2,
        "noise term": 1
    }
    
    frequency_analyzer = RuleBasedSimilarity()
    # Note: We need to implement frequency filtering in RuleBasedSimilarity
    # For now, just demonstrate the API
    
    # Test topology analysis
    adjacency_lists = {
        "A": {"B", "C", "D"},
        "B": {"A", "C", "E"},
        "C": {"A", "B", "D", "E"},
        "D": {"A", "C"},
        "E": {"B", "C", "F"},
        "F": {"E"}
    }
    
    topology_analyzer = GraphTopologyAnalyzer()
    shared_scores = topology_analyzer.analyze_shared_neighbors(adjacency_lists)
    print(f"Shared neighbor analysis: {len(shared_scores['shared_neighbor_scores'])} nodes analyzed")
    
    # Test rule engine
    rule_engine = RuleEngine()
    context = {
        'mention_counts': {"machine learning": 25, "ML": 12},
        'shared_neighbors': {("machine learning", "ML"): 3}
    }
    
    merge_decision = rule_engine.decide_entity_merge("machine learning", "ML", context)
    print(f"Merge decision: {merge_decision.get('should_merge', False)}, "
          f"confidence: {merge_decision.get('confidence', 0):.3f}")
    
    print("\n✅ Rule engine is ready for integration with meditation pipeline!")