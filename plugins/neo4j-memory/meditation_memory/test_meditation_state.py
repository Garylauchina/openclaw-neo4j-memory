#!/usr/bin/env python3
"""
Issue #46: 冥思状态持久化单元测试
"""

import sys
import os
import json
import tempfile
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meditation_state import (
    MeditationStatus,
    StepStats,
    MeditationState,
    MeditationStateManager
)


def test_meditation_status_enum():
    """测试 1: 冥思状态枚举"""
    print("🔍 测试 1: 冥思状态枚举")
    print("-" * 60)
    
    assert MeditationStatus.PENDING.value == "pending"
    assert MeditationStatus.IN_PROGRESS.value == "in_progress"
    assert MeditationStatus.COMPLETED.value == "completed"
    assert MeditationStatus.FAILED.value == "failed"
    assert MeditationStatus.INTERRUPTED.value == "interrupted"
    
    print(f"  ✅ PENDING: {MeditationStatus.PENDING.value}")
    print(f"  ✅ IN_PROGRESS: {MeditationStatus.IN_PROGRESS.value}")
    print(f"  ✅ COMPLETED: {MeditationStatus.COMPLETED.value}")
    print(f"  ✅ FAILED: {MeditationStatus.FAILED.value}")
    print(f"  ✅ INTERRUPTED: {MeditationStatus.INTERRUPTED.value}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_step_stats():
    """测试 2: 步骤统计"""
    print("🔍 测试 2: 步骤统计")
    print("-" * 60)
    
    stats = StepStats(step_num=2, processed=100, pruned=20, merged=15)
    
    # 验证 to_dict
    stats_dict = stats.to_dict()
    assert stats_dict["step_num"] == 2
    assert stats_dict["processed"] == 100
    assert stats_dict["pruned"] == 20
    assert stats_dict["merged"] == 15
    
    # 验证 from_dict
    stats2 = StepStats.from_dict(stats_dict)
    assert stats2.step_num == 2
    assert stats2.processed == 100
    
    print(f"  ✅ step_num: {stats.step_num}")
    print(f"  ✅ processed: {stats.processed}")
    print(f"  ✅ pruned: {stats.pruned}")
    print(f"  ✅ merged: {stats.merged}")
    print(f"  ✅ to_dict/from_dict: OK")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_meditation_state_serialization():
    """测试 3: 冥思状态序列化"""
    print("🔍 测试 3: 冥思状态序列化")
    print("-" * 60)
    
    state = MeditationState.create_new("test_run_001")
    state.current_step = 3
    state.status = MeditationStatus.IN_PROGRESS.value
    
    # 添加已处理节点
    state.processed_nodes[2] = {"node1", "node2", "node3"}
    state.processed_nodes[3] = {"node4", "node5"}
    
    # 验证 to_dict
    state_dict = state.to_dict()
    assert state_dict["run_id"] == "test_run_001"
    assert state_dict["current_step"] == 3
    assert state_dict["status"] == "in_progress"
    assert "node1" in state_dict["processed_nodes"]["2"]
    
    # 验证 from_dict
    state2 = MeditationState.from_dict(state_dict)
    assert state2.run_id == "test_run_001"
    assert state2.current_step == 3
    assert "node1" in state2.processed_nodes[2]
    
    print(f"  ✅ run_id: {state.run_id}")
    print(f"  ✅ current_step: {state.current_step}")
    print(f"  ✅ status: {state.status}")
    print(f"  ✅ processed_nodes: {len(state.processed_nodes)} steps")
    print(f"  ✅ to_dict/from_dict: OK")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_state_manager_persistence():
    """测试 4: 状态管理器持久化"""
    print("🔍 测试 4: 状态管理器持久化")
    print("-" * 60)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MeditationStateManager(state_dir=tmpdir)
        
        # 创建状态
        state = manager.create_state("test_run_002")
        assert state.run_id == "test_run_002"
        assert state.status == MeditationStatus.PENDING.value
        
        # 更新状态
        manager.update_status(MeditationStatus.IN_PROGRESS)
        manager.update_step(2)
        manager.save()  # 保存状态
        
        # 标记节点已处理
        manager.mark_node_processed(2, "node_001")
        manager.mark_node_processed(2, "node_002")
        manager.save()  # 保存状态
        
        # 验证幂等性
        assert manager.is_node_processed(2, "node_001") == True
        assert manager.is_node_processed(2, "node_003") == False
        
        # 获取未处理节点
        all_nodes = ["node_001", "node_002", "node_003", "node_004"]
        unprocessed = manager.get_unprocessed_nodes(2, all_nodes)
        assert len(unprocessed) == 2
        assert "node_003" in unprocessed
        assert "node_004" in unprocessed
        
        # 重新加载状态
        manager2 = MeditationStateManager(state_dir=tmpdir)
        loaded_state = manager2.load_state("test_run_002")
        print(f"    加载状态：run_id={loaded_state.run_id if loaded_state else None}, step={loaded_state.current_step if loaded_state else None}")
        assert loaded_state is not None, "加载状态失败"
        assert loaded_state.current_step == 2, f"期望 step=2，实际={loaded_state.current_step}"
        assert "node_001" in loaded_state.processed_nodes.get(2, set()), "node_001 不在已处理列表中"
        
        print(f"  ✅ create_state: OK")
        print(f"  ✅ update_status: OK")
        print(f"  ✅ update_step: OK")
        print(f"  ✅ mark_node_processed: OK")
        print(f"  ✅ is_node_processed: OK")
        print(f"  ✅ get_unprocessed_nodes: OK")
        print(f"  ✅ load_state: OK")
        print(f"  ✅ 测试通过")
    print()
    return True


def test_state_manager_recovery():
    """测试 5: 中断恢复"""
    print("🔍 测试 5: 中断恢复")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MeditationStateManager(state_dir=tmpdir)
        
        # 创建并模拟中断的状态
        state1 = manager.create_state("interrupted_run")
        manager.update_status(MeditationStatus.IN_PROGRESS)
        manager.update_step(4)
        manager.mark_node_processed(2, "node_001")
        manager.mark_node_processed(3, "node_002")
        manager.mark_node_processed(4, "node_003")
        
        # 创建已完成的状态
        state2 = manager.create_state("completed_run")
        manager.update_status(MeditationStatus.COMPLETED)
        manager.update_step(6)
        
        # 获取未完成的状态
        manager2 = MeditationStateManager(state_dir=tmpdir)
        incomplete = manager2.get_incomplete_states()
        
        assert len(incomplete) == 1
        assert incomplete[0].run_id == "interrupted_run"
        assert incomplete[0].current_step == 4
        
        print(f"  ✅ 创建中断状态：interrupted_run (step=4)")
        print(f"  ✅ 创建完成状态：completed_run (step=6)")
        print(f"  ✅ get_incomplete_states: {len(incomplete)} 个未完成")
        print(f"  ✅ 恢复点：step={incomplete[0].current_step}")
        print(f"  ✅ 测试通过")
    print()
    return True


def test_state_manager_cleanup():
    """测试 6: 状态文件清理"""
    print("🔍 测试 6: 状态文件清理")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MeditationStateManager(state_dir=tmpdir)
        
        # 创建多个状态
        for i in range(5):
            state = manager.create_state(f"run_{i:03d}")
            if i < 3:
                manager.update_status(MeditationStatus.COMPLETED)
            else:
                manager.update_status(MeditationStatus.IN_PROGRESS)
        
        # 清理（应该只清理已完成的）
        cleaned = manager.cleanup_old_states(days=0)  # 清理所有
        
        # 验证剩余文件
        remaining_files = list(manager.state_dir.glob("*.json"))
        # 已完成的 3 个被清理，未完成的 2 个保留
        assert len(remaining_files) == 2
        
        print(f"  ✅ 创建 5 个状态（3 个完成，2 个进行中）")
        print(f"  ✅ cleanup_old_states: 清理 {cleaned} 个")
        print(f"  ✅ 剩余文件：{len(remaining_files)} 个")
        print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #46: 冥思状态持久化单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("冥思状态枚举", test_meditation_status_enum),
        ("步骤统计", test_step_stats),
        ("冥思状态序列化", test_meditation_state_serialization),
        ("状态管理器持久化", test_state_manager_persistence),
        ("中断恢复", test_state_manager_recovery),
        ("状态文件清理", test_state_manager_cleanup)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ❌ 测试失败：{e}")
            print()
    
    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"       错误：{error}")
    
    print()
    print(f"总计：{passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
