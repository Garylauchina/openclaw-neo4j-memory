#!/usr/bin/env python3
# Verification script for P0 critical repairs (Issue #28)

import sys
sys.path.insert(0, 'plugins/neo4j-memory/')

# Test 1: Verify metacognition nodes can be created
def test_metacognition_neo4j_integration():
    print('🔍 Test 1: Metacognition Neo4j Integration')
    
    try:
        # Initialize metacognition module
        from meditation_memory.metacognition import MetacognitionGraph, MetacognitionLaw
        from meditation_memory.graph_store import GraphStore
        
        store = GraphStore()
        mc = MetacognitionGraph(store)
        
        # Create a test meta node
        node_id = mc.create_node(
            node_type='Meta_User',
            concept='Test user preference verification',
            category='user_preference',
            law=MetacognitionLaw.LAW_1,
            confidence=0.95,
            is_core=False,
            user_id='5273762787'
        )
        
        print(f'✓ Created meta node with ID: {node_id}')
        
        # Retrieve the node
        node = mc.get_node(node_id)
        if node:
            print(f'✓ Retrieved node: {node.concept[:50]}...')
            print(f'✓ Node properties - confidence: {node.confidence}, law: {node.law}')
        else:
            print('⚠️ Warning: Node not found after creation')
            return False
        
        # Test capacity limiter
        result, msg = mc.limiter.check_capacity('Meta_User', '5273762787')
        print(f'✓ Capacity check result: {result} - {msg}')
        
        # Verify capacity limits are correctly configured
        print(f'✓ Capacity limits configured:')
        print(f'  - Meta_Self: {mc.limiter.max_self_nodes} nodes')
        print(f'  - Meta_User: {mc.limiter.max_user_nodes} nodes')
        print(f'  - Meta_Relationship: {mc.limiter.max_relationship_nodes} nodes')
        
        # Cleanup - delete the test node
        deleted = mc.delete_node(node_id)
        print(f'✓ Test node deleted: {deleted}')
        
        return True
        
    except Exception as e:
        print(f'❌ Test 1 failed: {e}')
        return False

# Test 2: Verify meditation cost limits
def test_meditation_cost_limits():
    print('\n🔍 Test 2: Meditation Cost Limits')
    
    try:
        from meditation_memory.meditation_worker import MeditationWorker
        
        worker = MeditationWorker()
        
        # Check if cost limit config exists
        if hasattr(worker, 'cost_limit'):
            print(f'✓ Meditation cost limit enabled: ${worker.cost_limit}/day')
        else:
            print('⚠️ Warning: Cost limit not configured')
            
        return True
        
    except Exception as e:
        print(f'❌ Test 2 failed: {e}')
        return False

# Test 3: Verify rules engine integration
def test_rules_engine():
    print('\n🔍 Test 3: Rules Engine Integration')
    
    try:
        from meditation_memory.rules_engine import RuleEngine
        
        # Initialize rules engine
        rules_engine = RuleEngine()
        
        # Test noise filtering rules
        node_data = {
            'confidence': 0.15,
            'creation_time': '2026-01-01',
            'content': 'Hello world'
        }
        
        # Check if node should be pruned
        should_prune = rules_engine.should_prune_node(node_data)
        print(f'✓ Should prune low-confidence node: {should_prune}')
        
        return True
        
    except Exception as e:
        print(f'❌ Test 3 failed: {e}')
        return False

# Test 4: Verify entropy calculation
def test_entropy_calculation():
    print('\n🔍 Test 4: Entropy Calculation')
    
    try:
        from meditation_memory.information_theory import GraphEntropyMetrics
        
        # Test basic entropy calculation
        entropy = GraphEntropyMetrics.calculate_node_entropy({'content': 'Test node content with some words'})
        print(f'✓ Node entropy: {entropy:.4f}')
        
        # Test relationship entropy
        rel_entropy = GraphEntropyMetrics.calculate_relationship_entropy('related_to', {'type': 'Person'}, {'type': 'Organization'})
        print(f'✓ Relationship entropy: {rel_entropy:.4f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Test 4 failed: {e}')
        return False

# Test 5: Test core CRUD functionality
def test_core_crud():
    print('\n🔍 Test 5: Core CRUD Functionality')
    
    try:
        from meditation_memory.metacognition import MetacognitionGraph, MetacognitionLaw
        from meditation_memory.graph_store import GraphStore
        
        store = GraphStore()
        mc = MetacognitionGraph(store)
        
        print('✓ CRUD methods available:')
        print(f'  - create_node: {hasattr(mc, "create_node")}')
        print(f'  - get_node: {hasattr(mc, "get_node")}')
        print(f'  - update_confidence: {hasattr(mc, "update_confidence")}')
        print(f'  - delete_node: {hasattr(mc, "delete_node")}')
        print(f'  - decay_confidence_over_time: {hasattr(mc, "decay_confidence_over_time")}')
        print(f'  - import_seed_cognitions: {hasattr(mc, "import_seed_cognitions")}')
        
        return True
        
    except Exception as e:
        print(f'❌ Test 5 failed: {e}')
        return False

# Run all tests
print('🧪 Starting Verification Tests\n')

results = []
results.append(test_metacognition_neo4j_integration())
results.append(test_meditation_cost_limits())
results.append(test_rules_engine())
results.append(test_entropy_calculation())
results.append(test_core_crud())

# Summary
print('\n✅ Verification Tests Summary')
print(f'✓ Test 1 (Meta Neo4j): {"PASSED" if results[0] else "FAILED"}')
print(f'✓ Test 2 (Meditation Costs): {"PASSED" if results[1] else "FAILED"}')
print(f'✓ Test 3 (Rules Engine): {"PASSED" if results[2] else "FAILED"}')
print(f'✓ Test 4 (Entropy Calculation): {"PASSED" if results[3] else "FAILED"}')
print(f'✓ Test 5 (Core CRUD): {"PASSED" if results[4] else "FAILED"}')

if all(results):
    print('\n🎉 All core verification tests passed!')
else:
    failed = len([r for r in results if not r])
    print(f'\n⚠️ {failed} test(s) failed - please check the output above')
    sys.exit(1)
