"""
冥思成本保护配置模块（Issue #37）

防止 LLM 调用成本失控，提供多层级预算保护：
  1. 单次冥思预算上限
  2. 单次冥思 LLM 调用次数上限
  3. 每日预算上限
  4. 预算分配策略（按步骤分配）
  5. 降级策略（预算超支时的处理）
"""

import os
from dataclasses import dataclass, field


@dataclass
class MeditationCostConfig:
    """
    冥思成本保护配置
    
    防止 LLM 调用成本失控，提供多层级预算保护。
    """
    
    # 单次冥思最大成本（美元）
    max_meditation_budget_per_run: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_MAX_BUDGET_PER_RUN", "0.10")
        )
    )
    
    # 单次冥思最大 LLM 调用次数
    max_llm_calls_per_run: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MAX_LLM_CALLS_PER_RUN", "50")
        )
    )
    
    # 预算分配策略（按冥思步骤分配百分比）
    # Step 2: 噪声过滤 - 20%
    step2_pruning_budget_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STEP2_BUDGET_RATIO", "0.20")
        )
    )
    # Step 3: 实体合并 - 20%
    step3_merging_budget_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STEP3_BUDGET_RATIO", "0.20")
        )
    )
    # Step 4: 关系重标注 - 30%
    step4_relabeling_budget_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STEP4_BUDGET_RATIO", "0.30")
        )
    )
    # Step 5: 元知识蒸馏 - 20%
    step5_distillation_budget_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STEP5_BUDGET_RATIO", "0.20")
        )
    )
    # Step 6: 策略蒸馏 - 10%
    step6_strategy_budget_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STEP6_BUDGET_RATIO", "0.10")
        )
    )
    
    # 降级策略阈值
    # 警告阈值：达到预算的 80% 时发出警告
    warning_threshold_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_WARNING_THRESHOLD", "0.80")
        )
    )
    # 跳过非关键步骤阈值：达到预算的 90% 时跳过元知识蒸馏
    skip_non_critical_threshold_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_SKIP_NON_CRITICAL_THRESHOLD", "0.90")
        )
    )
    # 紧急停止阈值：达到预算的 100% 时终止冥思
    emergency_stop_threshold_ratio: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_EMERGENCY_STOP_THRESHOLD", "1.00")
        )
    )
    
    def validate_budget_ratios(self) -> bool:
        """验证预算分配比例总和是否为 1.0"""
        total = (
            self.step2_pruning_budget_ratio +
            self.step3_merging_budget_ratio +
            self.step4_relabeling_budget_ratio +
            self.step5_distillation_budget_ratio +
            self.step6_strategy_budget_ratio
        )
        # 允许 0.01 的误差
        return abs(total - 1.0) < 0.01
    
    def get_step_budget(self, step_num: int, total_budget: float) -> float:
        """获取指定步骤的预算分配"""
        ratios = {
            2: self.step2_pruning_budget_ratio,
            3: self.step3_merging_budget_ratio,
            4: self.step4_relabeling_budget_ratio,
            5: self.step5_distillation_budget_ratio,
            6: self.step6_strategy_budget_ratio
        }
        return total_budget * ratios.get(step_num, 0.0)


@dataclass
class BudgetStatus:
    """
    预算状态跟踪
    
    用于在冥思过程中跟踪当前成本和 LLM 调用次数。
    """
    
    # 当前总成本（美元）
    total_cost: float = 0.0
    
    # 当前 LLM 调用次数
    llm_calls: int = 0
    
    # 处理的节点数
    nodes_processed: int = 0
    
    # 预算状态：within_limit / warning / critical / exceeded
    budget_status: str = "within_limit"
    
    # 开始时间
    start_time: str = ""
    
    # 结束时间
    end_time: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_cost": self.total_cost,
            "llm_calls": self.llm_calls,
            "nodes_processed": self.nodes_processed,
            "cost_per_node": self.total_cost / max(1, self.nodes_processed),
            "budget_status": self.budget_status,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
    
    def add_cost(self, cost: float, llm_calls: int = 1):
        """增加成本"""
        self.total_cost += cost
        self.llm_calls += llm_calls
    
    def check_budget(self, config: MeditationCostConfig) -> str:
        """
        检查预算状态
        
        返回：within_limit / warning / critical / exceeded
        """
        ratio = self.total_cost / max(0.001, config.max_meditation_budget_per_run)
        
        if ratio >= config.emergency_stop_threshold_ratio:
            self.budget_status = "exceeded"
        elif ratio >= config.skip_non_critical_threshold_ratio:
            self.budget_status = "critical"
        elif ratio >= config.warning_threshold_ratio:
            self.budget_status = "warning"
        else:
            self.budget_status = "within_limit"
        
        return self.budget_status
