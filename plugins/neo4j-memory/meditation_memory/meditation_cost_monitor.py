"""
冥思成本监控集成模块（Issue #41）

在冥思流水线中集成成本监控，实现预算保护：
  1. 每个步骤检查预算状态
  2. 降级策略（警告/跳过/停止）
  3. 成本日志记录
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

# 支持直接运行和模块导入两种模式
try:
    from .meditation_cost_config import MeditationCostConfig, BudgetStatus
except ImportError:
    from meditation_cost_config import MeditationCostConfig, BudgetStatus

logger = logging.getLogger(__name__)


class MeditationCostMonitor:
    """
    冥思成本监控器
    
    集成到 MeditationWorker 中，负责：
    - 跟踪当前成本和 LLM 调用次数
    - 每个步骤前检查预算状态
    - 触发降级策略
    - 记录成本日志
    """
    
    def __init__(self, cost_config: MeditationCostConfig):
        self.cost_config = cost_config
        self.budget_status = BudgetStatus()
        
        # 各步骤成本明细
        self.step_costs: Dict[int, float] = {
            2: 0.0,
            3: 0.0,
            4: 0.0,
            5: 0.0,
            6: 0.0
        }
        
        # 验证预算分配比例
        if not self.cost_config.validate_budget_ratios():
            logger.warning("预算分配比例总和不等于 1.0，可能配置有误")
    
    def start_meditation(self):
        """开始冥思，初始化预算状态"""
        self.budget_status.start_time = datetime.now().isoformat()
        self.budget_status.total_cost = 0.0
        self.budget_status.llm_calls = 0
        self.budget_status.nodes_processed = 0
        self.budget_status.budget_status = "within_limit"
        self.step_costs = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
        
        logger.info(f"冥思开始，预算上限：${self.cost_config.max_meditation_budget_per_run:.4f}, "
                   f"LLM 调用上限：{self.cost_config.max_llm_calls_per_run}次")
    
    def end_meditation(self):
        """结束冥思，记录最终状态"""
        self.budget_status.end_time = datetime.now().isoformat()
        self.log_cost_report()
    
    def add_cost(self, step_num: int, cost: float, llm_calls: int = 1, nodes_processed: int = 0):
        """
        增加成本
        
        Args:
            step_num: 冥思步骤编号（2-6）
            cost: 成本（美元）
            llm_calls: LLM 调用次数
            nodes_processed: 处理的节点数
        """
        self.budget_status.add_cost(cost, llm_calls)
        self.budget_status.nodes_processed += nodes_processed
        
        # 记录步骤成本
        if step_num in self.step_costs:
            self.step_costs[step_num] += cost
        
        # 检查预算状态
        self.check_budget()
    
    def check_budget(self) -> str:
        """
        检查预算状态
        
        Returns:
            budget_status: within_limit / warning / critical / exceeded
        """
        return self.budget_status.check_budget(self.cost_config)
    
    def should_skip_step(self, step_num: int) -> bool:
        """
        判断是否应该跳过当前步骤
        
        Args:
            step_num: 冥思步骤编号
            
        Returns:
            True: 应该跳过，False: 继续执行
        """
        status = self.budget_status.budget_status
        
        # exceeded: 紧急停止，跳过所有后续步骤
        if status == "exceeded":
            logger.warning(f"预算已超支，跳过 Step {step_num}")
            return True
        
        # critical: 跳过非关键步骤（Step 5: 元知识蒸馏）
        if status == "critical" and step_num == 5:
            logger.warning(f"预算紧张，跳过非关键步骤 Step {step_num}（元知识蒸馏）")
            return True
        
        return False
    
    def should_simplify_step(self, step_num: int) -> bool:
        """
        判断是否应该简化当前步骤（使用更少的 LLM 调用）
        
        Args:
            step_num: 冥思步骤编号
            
        Returns:
            True: 应该简化，False: 正常执行
        """
        status = self.budget_status.budget_status
        
        # warning: 简化后续步骤
        if status == "warning":
            logger.info(f"预算达到警告线，简化 Step {step_num}")
            return True
        
        return False
    
    def get_step_budget(self, step_num: int) -> float:
        """获取指定步骤的预算分配"""
        return self.cost_config.get_step_budget(step_num, self.cost_config.max_meditation_budget_per_run)
    
    def log_cost_report(self):
        """输出成本报告"""
        report = self.get_cost_report()
        
        logger.info("=" * 70)
        logger.info("冥思成本报告")
        logger.info("=" * 70)
        logger.info(f"总成本：${report['total_cost']:.4f}")
        logger.info(f"LLM 调用次数：{report['llm_calls']}")
        logger.info(f"处理节点数：{report['nodes_processed']}")
        logger.info(f"单位成本：${report['cost_per_node']:.6f}/节点")
        logger.info(f"预算状态：{report['budget_status']}")
        logger.info(f"持续时间：{report.get('duration_seconds', 0):.1f}秒")
        logger.info("")
        logger.info("步骤成本明细:")
        for step, cost in report['step_costs'].items():
            budget = self.get_step_budget(step)
            logger.info(f"  Step {step}: ${cost:.4f} / 预算 ${budget:.4f} ({cost/max(0.001, budget)*100:.1f}%)")
        logger.info("=" * 70)
    
    def get_cost_report(self) -> Dict[str, Any]:
        """获取成本报告字典"""
        report = self.budget_status.to_dict()
        report['step_costs'] = self.step_costs
        
        # 计算持续时间
        if self.budget_status.start_time and self.budget_status.end_time:
            start = datetime.fromisoformat(self.budget_status.start_time)
            end = datetime.fromisoformat(self.budget_status.end_time)
            report['duration_seconds'] = (end - start).total_seconds()
        
        return report
    
    def is_within_llm_limit(self) -> bool:
        """检查是否在 LLM 调用次数限制内"""
        return self.budget_status.llm_calls < self.cost_config.max_llm_calls_per_run
    
    def get_remaining_budget(self) -> float:
        """获取剩余预算"""
        return max(0.0, self.cost_config.max_meditation_budget_per_run - self.budget_status.total_cost)
    
    def get_remaining_llm_calls(self) -> int:
        """获取剩余 LLM 调用次数"""
        return max(0, self.cost_config.max_llm_calls_per_run - self.budget_status.llm_calls)
