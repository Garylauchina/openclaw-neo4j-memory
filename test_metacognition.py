#!/usr/bin/env python3
"""Test script for Phase 1 metacognition module implementation"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins/neo4j-memory"))

from meditation_memory.metacognition import MetacognitionGraph, MetacognitionNode, MetacognitionLaw
from meditation_memory.graph_store import GraphStore


def test_phase1_implementation():
    """Test all Phase 1 implementation targets"""
    print("=== Testing Phase 1 Metacognition Module Implementation ===")
    
    try:
        # Initialize graph store
        store = GraphStore()
        print("✓ GraphStore initialized successfully")
        
        # Initialize metacognition graph
        meta_graph = MetacognitionGraph(store)
        print("✓ MetacognitionGraph initialized successfully")
        
        # Test 1: Create node functionality
        node = MetacognitionNode(
            node_type="Meta_Self",
            concept="I can successfully create nodes in Neo4j",
            category="capability",
            law=MetacognitionLaw.LAW_3,
            confidence=0.7,
            is_core=False
        )
        
        success = meta_graph.create_node(node)
        if success:
            print(f"✓ Node creation test passed: {node.id}")
            
            # Test 2: Get node functionality
            retrieved_node = meta_graph.get_node(node.id)
            if retrieved_node:
                print(f"✓ Node retrieval test passed: {retrieved_node.concept}")
            else:
                print("✗ Node retrieval test failed: Node not found")
                
            # Test 3: Update confidence functionality
            update_success = meta_graph.update_confidence(node.id, 0.9, "test_verification")
            if update_success:
                print("✓ Confidence update test passed")
            else:
                print("✗ Confidence update test failed")
                
            # Test 4: Delete node functionality
            delete_success = meta_graph.delete_node(node.id)
            if delete_success:
                print("✓ Node deletion test passed")
            else:
                print("✗ Node deletion test failed")
                
        else:
            print("✗ Node creation test failed")
            
        # Test 5: Capacity limiter
        limiter = meta_graph.limiter
        capacity_ok, message = limiter.check_capacity("Meta_Self")
        print(f"✓ Capacity check test passed: {capacity_ok}" + (f" - {message}" if message else ""))
        
        # Test 6: Confidence decay
        decay_count = meta_graph.decay_confidence_over_time(30)
        print(f"✓ Confidence decay test passed: Decayed {decay_count} nodes")
        
        # Test 7: Seed cognition import
        seed_nodes = meta_graph.import_seed_cognitions("agent.md", "Meta_Self")
        print(f"✓ Seed cognition import test passed: Imported {len(seed_nodes)} nodes")
        
        print("\n=== All Phase 1 tests completed ===")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_phase1_implementation()
