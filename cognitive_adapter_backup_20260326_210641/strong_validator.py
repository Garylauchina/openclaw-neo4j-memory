#!/usr/bin/env python3
"""
Strong Validator - 强约束验证
核心：验证必须影响 Belief + RQS + 触发Replan
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from datetime import datetime

class ValidationResult:
    """验证结果"""
    
    def __init__(self, 
                 status: str,
                 error: float,
                 confidence: float,
                 details: Dict[str, Any]):
        self.status = status  # "accurate", "acceptable", "wrong"
        self.error = error    # 相对误差
        self.confidence = confidence
        self.details = details
        
        # 影响因子
        self.belief_impact = self._calculate_belief_impact()
        self.rqs_impact = self._calculate_rqs_impact()
        self.requires_replan = status == "wrong"
        
    def _calculate_belief_impact(self) -> float:
        """计算信念影响"""
        if self.status == "accurate":
            return 0.1  # 轻微正向影响
        elif self.status == "acceptable":
            return 0.0  # 无影响
        else:  # wrong
            return -0.3  # 显著负向影响
    
    def _calculate_rqs_impact(self) -> float:
        """计算RQS影响"""
        if self.status == "accurate":
            return 0.05  # 轻微提升
        elif self.status == "acceptable":
            return 0.0   # 无影响
        else:  # wrong
            return -0.3  # 显著降低
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "error": self.error,
            "confidence": self.confidence,
            "belief_impact": self.belief_impact,
            "rqs_impact": self.rqs_impact,
            "requires_replan": self.requires_replan,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }

class StrongValidator:
    """强约束验证器"""
    
    def __init__(self, 
                 graph=None,
                 rqs_system=None,
                 belief_system=None):
        self.graph = graph
        self.rqs_system = rqs_system
        self.belief_system = belief_system
        
        # 验证历史
        self.validation_history: List[ValidationResult] = []
        
        # 统计
        self.stats = {
            "total_validations": 0,
            "accurate": 0,
            "acceptable": 0,
            "wrong": 0,
            "avg_error": 0.0,
            "replans_triggered": 0,
            "belief_updates": 0,
            "rqs_updates": 0
        }
        
        # 阈值配置
        self.thresholds = {
            "accurate": 0.01,   # 误差 < 1%
            "acceptable": 0.05,  # 误差 < 5%
            "wrong": 0.05       # 误差 >= 5%
        }
    
    def validate(self, 
                internal_result: Any,
                api_result: Any,
                context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        强约束验证
        
        Args:
            internal_result: 内部推理结果
            api_result: API真实结果
            context: 上下文信息
            
        Returns:
            验证结果
        """
        self.stats["total_validations"] += 1
        
        # 计算误差
        error = self._calculate_error(internal_result, api_result)
        
        # 确定状态
        status = self._determine_status(error)
        
        # 计算置信度
        confidence = self._calculate_confidence(error, context)
        
        # 创建验证结果
        details = {
            "internal_result": internal_result,
            "api_result": api_result,
            "absolute_error": abs(internal_result - api_result) if isinstance(internal_result, (int, float)) else None,
            "context": context or {}
        }
        
        result = ValidationResult(status, error, confidence, details)
        
        # 记录历史
        self.validation_history.append(result)
        
        # 更新统计
        self._update_stats(result)
        
        # ❗ 强约束影响系统
        self._apply_strong_constraints(result, context)
        
        return result
    
    def _calculate_error(self, internal: Any, api: Any) -> float:
        """计算相对误差"""
        try:
            if isinstance(internal, (int, float)) and isinstance(api, (int, float)):
                if api == 0:
                    return abs(internal)  # 避免除以零
                return abs(internal - api) / abs(api)
            else:
                # 对于非数值，使用字符串相似度
                internal_str = str(internal)
                api_str = str(api)
                
                if internal_str == api_str:
                    return 0.0
                
                # 简单相似度计算
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, internal_str, api_str).ratio()
                return 1.0 - similarity
                
        except Exception as e:
            print(f"   ⚠️  误差计算失败: {e}")
            return 1.0  # 最大误差
    
    def _determine_status(self, error: float) -> str:
        """确定验证状态"""
        if error < self.thresholds["accurate"]:
            return "accurate"
        elif error < self.thresholds["acceptable"]:
            return "acceptable"
        else:
            return "wrong"
    
    def _calculate_confidence(self, error: float, context: Optional[Dict[str, Any]]) -> float:
        """计算置信度"""
        # 基础置信度（基于误差）
        base_confidence = 1.0 - min(1.0, error * 10)  # 误差越大，置信度越低
        
        # 上下文调整
        context_boost = 0.0
        if context:
            if context.get("source") == "real_world_api":
                context_boost = 0.1
            if context.get("validated", False):
                context_boost += 0.05
        
        confidence = min(1.0, base_confidence + context_boost)
        
        return max(0.1, confidence)  # 保持最小置信度
    
    def _apply_strong_constraints(self, result: ValidationResult, context: Optional[Dict[str, Any]]):
        """应用强约束影响系统"""
        
        print(f"\n   🔒 应用强约束:")
        print(f"     状态: {result.status}")
        print(f"     误差: {result.error:.3%}")
        print(f"     信念影响: {result.belief_impact:+.2f}")
        print(f"     RQS影响: {result.rqs_impact:+.2f}")
        print(f"     需要重规划: {result.requires_replan}")
        
        # 1. ❗ 影响Belief系统
        if self.belief_system and hasattr(self.belief_system, 'update_belief'):
            try:
                self.belief_system.update_belief(
                    evidence=result.details,
                    impact=result.belief_impact,
                    confidence=result.confidence
                )
                self.stats["belief_updates"] += 1
                print(f"     ✅ Belief系统已更新")
            except Exception as e:
                print(f"     ⚠️  Belief更新失败: {e}")
        
        # 2. ❗ 影响RQS系统
        if self.rqs_system and hasattr(self.rqs_system, 'adjust_score'):
            try:
                adjustment = result.rqs_impact * result.confidence
                self.rqs_system.adjust_score(adjustment)
                self.stats["rqs_updates"] += 1
                print(f"     ✅ RQS系统已调整: {adjustment:+.3f}")
            except Exception as e:
                print(f"     ⚠️  RQS调整失败: {e}")
        
        # 3. ❗ 影响图系统（如果可用）
        if self.graph and hasattr(self.graph, 'degrade_path'):
            if result.status == "wrong":
                try:
                    # 获取推理路径（从上下文）
                    inference_path = context.get("inference_path", []) if context else []
                    if inference_path:
                        self.graph.degrade_path(inference_path, degradation=0.3)
                        print(f"     ✅ 推理路径已降级")
                except Exception as e:
                    print(f"     ⚠️  路径降级失败: {e}")
        
        # 4. ❗ 触发重规划
        if result.requires_replan:
            self.stats["replans_triggered"] += 1
            print(f"     🚨 触发重规划")
            
            # 这里可以调用重规划系统
            self._trigger_replan(context)
    
    def _trigger_replan(self, context: Optional[Dict[str, Any]]):
        """触发重规划"""
        # 这里可以集成到现有的规划系统
        replan_context = {
            "reason": "validation_failed",
            "error_threshold": self.thresholds["wrong"],
            "original_context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"       重规划上下文: {replan_context}")
        
        # 在实际系统中，这里会调用规划器
        # planner.replan(replan_context)
    
    def _update_stats(self, result: ValidationResult):
        """更新统计信息"""
        if result.status == "accurate":
            self.stats["accurate"] += 1
        elif result.status == "acceptable":
            self.stats["acceptable"] += 1
        else:
            self.stats["wrong"] += 1
        
        # 更新平均误差
        total_error = sum(r.error for r in self.validation_history)
        self.stats["avg_error"] = total_error / len(self.validation_history)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if self.stats["total_validations"] == 0:
            return {
                "has_data": False,
                "message": "尚无验证数据"
            }
        
        accuracy_rate = self.stats["accurate"] / self.stats["total_validations"]
        error_rate = self.stats["wrong"] / self.stats["total_validations"]
        
        return {
            "has_data": True,
            "summary": {
                "total_validations": self.stats["total_validations"],
                "accuracy_rate": accuracy_rate,
                "error_rate": error_rate,
                "avg_error": self.stats["avg_error"],
                "replan_rate": self.stats["replans_triggered"] / self.stats["total_validations"]
            },
            "system_impact": {
                "belief_updates": self.stats["belief_updates"],
                "rqs_updates": self.stats["rqs_updates"],
                "replans_triggered": self.stats["replans_triggered"]
            },
            "thresholds": self.thresholds,
            "recent_validations": [
                {
                    "status": r.status,
                    "error": r.error,
                    "requires_replan": r.requires_replan
                }
                for r in self.validation_history[-5:]
            ] if self.validation_history else []
        }
    
    def print_report(self):
        """打印报告"""
        report = self.get_performance_report()
        
        if not report["has_data"]:
            print("   📊 尚无验证数据")
            return
        
        summary = report["summary"]
        impact = report["system_impact"]
        
        print(f"\n   📊 强约束验证器报告:")
        print(f"     性能:")
        print(f"       总验证次数: {summary['total_validations']}")
        print(f"       准确率: {summary['accuracy_rate']:.1%}")
        print(f"       错误率: {summary['error_rate']:.1%}")
        print(f"       平均误差: {summary['avg_error']:.3%}")
        print(f"       重规划率: {summary['replan_rate']:.1%}")
        
        print(f"     系统影响:")
        print(f"       Belief更新: {impact['belief_updates']}")
        print(f"       RQS更新: {impact['rqs_updates']}")
        print(f"       触发重规划: {impact['replans_triggered']}")
        
        print(f"     阈值配置:")
        for key, value in report['thresholds'].items():
            print(f"       {key}: {value:.1%}")
        
        if report['recent_validations']:
            print(f"     最近验证:")
            for i, val in enumerate(report['recent_validations']):
                symbol = "✅" if val['status'] == 'accurate' else "⚠️" if val['status'] == 'acceptable' else "❌"
                replan = "🔄" if val['requires_replan'] else ""
                print(f"       {i+1}. {symbol}{replan} {val['status']} (误差: {val['error']:.3%})")

def test_strong_validator():
    """测试强约束验证器"""
    print("🧪 测试 StrongValidator...")
    
    # 创建模拟系统
    class MockBeliefSystem:
        def update_belief(self, evidence, impact, confidence):
            print(f"      [MockBelief] 更新信念: 影响={impact}, 置信度={confidence}")
    
    class MockRQSSystem:
        def __init__(self):
            self.score = 0.7
        
        def adjust_score(self, adjustment):
            self.score += adjustment
            print(f"      [MockRQS] 调整分数: {adjustment:+.3f} → 新分数: {self.score:.3f}")
    
    class MockGraph:
        def degrade_path(self, path, degradation):
            print(f"      [MockGraph] 降级路径: {path}, 降级={degradation}")
    
    # 创建验证器
    validator = StrongValidator(
        graph=MockGraph(),
        rqs_system=MockRQSSystem(),
        belief_system=MockBeliefSystem()
    )
    
    # 测试用例
    test_cases = [
        {
            "internal": 6.912,
            "api": 6.9123,
            "context": {"source": "real_world_api", "query": "USD/CNY"},
            "description": "高度准确（误差0.004%）"
        },
        {
            "internal": 6.90,
            "api": 6.9123,
            "context": {"source": "real_world_api", "query": "USD/CNY"},
            "description": "可接受（误差0.18%）"
        },
        {
            "internal": 7.0,
            "api": 6.9123,
            "context": {"source": "real_world_api", "query": "USD/CNY", "inference_path": ["fx_model", "prediction"]},
            "description": "错误（误差1.27%）"
        },
        {
            "internal": "汇率是6.9",
            "api": "当前汇率6.9123",
            "context": {"query": "汇率信息"},
            "description": "文本验证"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试用例 {i}: {test_case['description']}")
        print(f"   内部结果: {test_case['internal']}")
        print(f"   API结果: {test_case['api']}")
        
        result = validator.validate(
            test_case["internal"],
            test_case["api"],
            test_case["context"]
        )
        
        print(f"   验证结果: {result.status} (误差: {result.error:.3%})")
    
    # 显示报告
    print(f"\n📋 最终报告:")
    validator.print_report()
    
    return validator

if __name__ == "__main__":
    test_strong_validator()