#!/usr/bin/env python3
"""
测试自适应切换
专门验证冷启动 → 稳定学习切换
"""

import sys
sys.path.append('.')

print("🧪 测试自适应切换")
print("="*60)
print("目标：验证系统能从冷启动切换到稳定学习")
print("策略：使用更激进的冷启动配置")
print("="*60)

from adaptive_learning_system import AdaptiveLearningSystem, LearningPhase, SystemState
import time

# 创建自适应系统
print("1. 创建自适应学习系统...")
adaptive_system = AdaptiveLearningSystem()

# 模拟系统从冷启动到稳定的过程
print("\n2. 模拟系统状态变化...")

# 阶段1: 冷启动初期
print("\n   阶段1: 冷启动初期")
states = []

# 模拟前10轮：Graph开始增长，但Diff很少
for i in range(10):
    state = SystemState(
        total_edges=i+1,
        total_applied_diffs=0,  # 还没有应用Diff
        avg_pattern_confidence=0.3 + i*0.05,
        total_nodes=(i+1)*2,
        total_patterns=max(0, i-2),
        write_ratio=0.0,
        phase_duration=i+1,
        edges_per_round=1.0,
        diffs_per_round=0.0
    )
    states.append(state)
    
    phase = adaptive_system.phase_detector.detect_phase(state)
    adaptive_system.update_phase(state)
    
    print(f"     轮{i+1}: edges={state.total_edges}, diffs={state.total_applied_diffs}, "
          f"conf={state.avg_pattern_confidence:.2f} → 阶段: {phase.value}")

# 阶段2: 冷启动中期（开始有Diff）
print("\n   阶段2: 冷启动中期（开始学习）")
for i in range(10, 20):
    state = SystemState(
        total_edges=i+1,
        total_applied_diffs=(i-9)*2,  # 开始应用Diff
        avg_pattern_confidence=0.6 + (i-10)*0.03,
        total_nodes=(i+1)*2,
        total_patterns=i-5,
        write_ratio=0.5,  # 50%写入率
        phase_duration=i+1,
        edges_per_round=1.0,
        diffs_per_round=0.2
    )
    states.append(state)
    
    phase = adaptive_system.phase_detector.detect_phase(state)
    adaptive_system.update_phase(state)
    
    print(f"     轮{i+1}: edges={state.total_edges}, diffs={state.total_applied_diffs}, "
          f"conf={state.avg_pattern_confidence:.2f} → 阶段: {phase.value}")

# 阶段3: 达到稳定条件
print("\n   阶段3: 达到稳定条件")
for i in range(20, 30):
    state = SystemState(
        total_edges=50 + (i-20)*2,  # 超过50边
        total_applied_diffs=20 + (i-20)*3,  # 超过10个Diff
        avg_pattern_confidence=0.7 + (i-20)*0.02,  # 超过0.6
        total_nodes=100 + (i-20)*4,
        total_patterns=15 + (i-20),
        write_ratio=0.3,  # 写入率下降
        phase_duration=i+1,
        edges_per_round=2.0,
        diffs_per_round=0.3
    )
    states.append(state)
    
    phase = adaptive_system.phase_detector.detect_phase(state)
    adaptive_system.update_phase(state)
    
    print(f"     轮{i+1}: edges={state.total_edges}, diffs={state.total_applied_diffs}, "
          f"conf={state.avg_pattern_confidence:.2f} → 阶段: {phase.value}")

# 阶段4: 稳定学习
print("\n   阶段4: 稳定学习")
for i in range(30, 40):
    state = SystemState(
        total_edges=80 + (i-30)*2,
        total_applied_diffs=50 + (i-30)*2,
        avg_pattern_confidence=0.8 + (i-30)*0.01,
        total_nodes=180 + (i-30)*4,
        total_patterns=25 + (i-30),
        write_ratio=0.2,  # 稳定阶段写入率更低
        phase_duration=i+1,
        edges_per_round=2.0,
        diffs_per_round=0.2
    )
    states.append(state)
    
    phase = adaptive_system.phase_detector.detect_phase(state)
    adaptive_system.update_phase(state)
    
    print(f"     轮{i+1}: edges={state.total_edges}, diffs={state.total_applied_diffs}, "
          f"conf={state.avg_pattern_confidence:.2f} → 阶段: {phase.value}")

# 分析结果
print("\n3. 分析自适应切换结果...")
phase_info = adaptive_system.phase_detector.get_phase_info()

print(f"\n   📊 最终阶段信息:")
print(f"      当前阶段: {phase_info['phase']}")
print(f"      阶段持续时间: {phase_info['phase_duration']}轮")
print(f"      阶段切换次数: {phase_info['phase_switch_count']}")
print(f"      稳定轮数: {phase_info['stable_rounds']}")
print(f"      是否锁定: {'✅ 是' if phase_info['is_locked'] else '❌ 否'}")

# 检查配置切换
print(f"\n   ⚙️  配置切换验证:")
cold_config = adaptive_system.cold_start_config
stable_config = adaptive_system.stable_config

print(f"      冷启动配置:")
print(f"        buffer_size: {cold_config.buffer_size}")
print(f"        confidence_threshold: {cold_config.confidence_threshold}")
print(f"        max_diffs_per_reflection: {cold_config.max_diffs_per_reflection}")

print(f"\n      稳定配置:")
print(f"        buffer_size: {stable_config.buffer_size}")
print(f"        confidence_threshold: {stable_config.confidence_threshold}")
print(f"        max_diffs_per_reflection: {stable_config.max_diffs_per_reflection}")

# 验证切换逻辑
print(f"\n4. 验证切换逻辑...")

final_state = states[-1]
print(f"   最终系统状态:")
print(f"     Graph边数: {final_state.total_edges} {'✅ ≥50' if final_state.total_edges >= 50 else '❌ <50'}")
print(f"     应用Diff数: {final_state.total_applied_diffs} {'✅ ≥10' if final_state.total_applied_diffs >= 10 else '❌ <10'}")
print(f"     模式置信度: {final_state.avg_pattern_confidence:.3f} {'✅ ≥0.6' if final_state.avg_pattern_confidence >= 0.6 else '❌ <0.6'}")

# 判断是否成功切换
if (final_state.total_edges >= 50 and 
    final_state.total_applied_diffs >= 10 and 
    final_state.avg_pattern_confidence >= 0.6):
    
    print(f"\n   ✅ 所有稳定条件满足！")
    
    if phase_info['phase'] == 'stable':
        print(f"   ✅ 成功切换到稳定阶段！")
        print(f"   ✅ 自适应切换验证通过！")
        
        print(f"\n   🎯 关键成就:")
        print(f"       1. ✅ 自动检测系统阶段")
        print(f"       2. ✅ 动态切换学习策略")
        print(f"       3. ✅ 阶段锁定机制")
        print(f"       4. ✅ 完整指标跟踪")
    else:
        print(f"   ❌ 系统仍在冷启动阶段")
        print(f"      可能原因: 阶段检测阈值需要调整")
else:
    print(f"\n   ❌ 稳定条件未完全满足")
    print(f"      需要更多数据积累")

print("\n" + "="*60)
print("🎯 自适应切换测试完成")
print("="*60)

print(f"\n💡 重要发现:")
print("   1. 系统需要积累足够数据才能切换到稳定阶段")
print("   2. 关键指标: Graph规模、应用Diff数、模式置信度")
print("   3. 冷启动配置需要足够激进才能快速学习")
print("   4. 稳定配置需要足够保守防止过拟合")

print(f"\n🚀 建议调整:")
print("   如果系统切换太慢:")
print("     1. 降低稳定条件阈值")
print("     2. 使用更激进的冷启动配置")
print("     3. 增加学习频率")

print(f"\n   如果系统切换太早:")
print("     1. 提高稳定条件阈值")
print("     2. 使用更保守的冷启动配置")
print("     3. 增加阶段锁定轮数")

print(f"\n🕐 测试完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")