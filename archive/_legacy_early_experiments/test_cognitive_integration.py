#!/usr/bin/env python3
"""
测试认知系统是否被OpenClaw实际调用
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

def test_actual_integration():
    """测试实际集成状态"""
    print("🔍 测试认知系统实际集成状态")
    print("=" * 60)
    
    # 1. 检查OpenClaw是否调用认知钩子
    print("1️⃣ 检查OpenClaw调用链...")
    
    # 创建调用日志文件
    call_log_path = "/Users/liugang/.openclaw/workspace/cognitive_call_log.json"
    
    # 模拟OpenClaw调用认知钩子
    try:
        import openclaw_cognitive_hook
        
        # 创建钩子实例
        hook = openclaw_cognitive_hook.OpenClawCognitiveHook()
        
        # 记录调用
        call_log = {
            "test_time": datetime.now().isoformat(),
            "hook_version": hook.hook_version,
            "hook_initialized": True,
            "cognitive_core_loaded": hook.cognitive_core is not None,
            "stats": hook.stats
        }
        
        with open(call_log_path, 'w', encoding='utf-8') as f:
            json.dump(call_log, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 认知钩子可创建: {hook.hook_version}")
        print(f"   📊 钩子统计: {hook.stats}")
        
    except Exception as e:
        print(f"   ❌ 认知钩子创建失败: {e}")
        return False
    
    # 2. 检查OpenClaw实际配置
    print("\n2️⃣ 检查OpenClaw实际配置...")
    
    config_path = "/Users/liugang/.openclaw/openclaw.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 检查关键配置
        has_cognitive = "cognitive" in config
        has_hooks = "hooks" in config
        has_memory_provider = "memory" in config and "provider" in config.get("memory", {})
        
        print(f"   ✅ OpenClaw配置可读取")
        print(f"   🔧 配置状态:")
        print(f"      cognitive配置: {'✅ 存在' if has_cognitive else '❌ 不存在'}")
        print(f"      hooks配置: {'✅ 存在' if has_hooks else '❌ 不存在'}")
        print(f"      memory.provider: {'✅ 存在' if has_memory_provider else '❌ 不存在'}")
        
        if not (has_cognitive or has_hooks or has_memory_provider):
            print("   ⚠️  OpenClaw配置中没有认知系统相关配置")
            
    except Exception as e:
        print(f"   ❌ 配置读取失败: {e}")
    
    # 3. 检查OpenClaw实际运行状态
    print("\n3️⃣ 检查OpenClaw实际运行状态...")
    
    try:
        # 检查OpenClaw进程
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        openclaw_processes = [line for line in result.stdout.split('\n') if 'openclaw' in line and 'grep' not in line]
        
        print(f"   📊 OpenClaw进程数: {len(openclaw_processes)}")
        for proc in openclaw_processes[:2]:
            print(f"      {proc[:80]}...")
        
    except Exception as e:
        print(f"   ❌ 进程检查失败: {e}")
    
    # 4. 测试记忆系统实际调用
    print("\n4️⃣ 测试记忆系统实际调用...")
    
    # 检查memory_search工具是否使用认知系统
    print("   🔍 检查memory_search工具...")
    
    # 查看memory-core插件源码
    memory_plugin_path = "/opt/homebrew/lib/node_modules/openclaw/dist/extensions/memory-core/index.js"
    if os.path.exists(memory_plugin_path):
        print(f"   ✅ memory-core插件存在: {memory_plugin_path}")
        
        # 检查是否提到认知系统
        with open(memory_plugin_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)
            
        if 'cognitive' in content.lower():
            print("   ✅ memory-core插件提到认知系统")
        else:
            print("   ❌ memory-core插件未提到认知系统")
    else:
        print(f"   ❌ memory-core插件不存在")
    
    # 5. 创建集成测试
    print("\n5️⃣ 创建集成测试...")
    
    test_query = "USD/CNY汇率是多少？"
    print(f"   测试查询: {test_query}")
    
    try:
        # 尝试通过认知系统处理
        result = hook.process_query_hook(test_query)
        
        print(f"   ✅ 认知系统处理成功")
        print(f"   结果类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   结果键: {list(result.keys())}")
        elif isinstance(result, str):
            print(f"   结果长度: {len(result)}字符")
            print(f"   结果预览: {result[:100]}...")
        
        # 记录测试结果
        test_result = {
            "test_time": datetime.now().isoformat(),
            "query": test_query,
            "success": True,
            "result_type": str(type(result)),
            "result_preview": str(result)[:200] if result else None
        }
        
        test_log_path = "/Users/liugang/.openclaw/workspace/cognitive_test_log.json"
        with open(test_log_path, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 测试日志已保存: {test_log_path}")
        
    except Exception as e:
        print(f"   ❌ 认知系统处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 最终结论
    print("\n" + "=" * 60)
    print("🎯 最终集成状态判断")
    print("=" * 60)
    
    # 检查所有证据
    evidence = {
        "hook_exists": os.path.exists("/Users/liugang/.openclaw/workspace/openclaw_cognitive_hook.py"),
        "hook_creatable": "openclaw_cognitive_hook" in sys.modules,
        "config_has_cognitive": has_cognitive if 'has_cognitive' in locals() else False,
        "config_has_hooks": has_hooks if 'has_hooks' in locals() else False,
        "memory_plugin_exists": os.path.exists(memory_plugin_path),
        "test_query_processed": 'result' in locals()
    }
    
    print("🔍 证据收集:")
    for key, value in evidence.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    # 判断集成状态
    true_count = sum(evidence.values())
    total_count = len(evidence)
    integration_ratio = true_count / total_count
    
    print(f"\n📊 集成度: {true_count}/{total_count} ({integration_ratio:.0%})")
    
    if integration_ratio >= 0.8:
        print("🎉 结论: 认知系统高度集成")
    elif integration_ratio >= 0.5:
        print("⚠️  结论: 认知系统部分集成")
    else:
        print("❌ 结论: 认知系统未集成")
    
    print("\n" + "=" * 60)
    return integration_ratio >= 0.5

def main():
    """主函数"""
    print("🚀 开始认知系统集成测试")
    print("=" * 60)
    
    try:
        integrated = test_actual_integration()
        
        if integrated:
            print("✅ 测试完成: 认知系统似乎已集成")
            print("💡 但需要验证OpenClaw是否实际调用")
        else:
            print("❌ 测试完成: 认知系统未集成")
            print("💡 需要创建真正的集成方案")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔧 建议下一步:")
    print("1. 创建OpenClaw插件包装认知系统")
    print("2. 或创建HTTP桥接服务")
    print("3. 或重写认知系统为OpenClaw插件")
    print("=" * 60)

if __name__ == "__main__":
    main()