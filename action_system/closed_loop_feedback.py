        self.stats = {
            "total_feedbacks": 0,
            "avg_feedback_score": 0.0,
            "replan_count": 0,
            "replan_rate": 0.0,
            "belief_update_count": 0,
            "meta_learning_count": 0,
            "feedback_trend": "stable",
            "time_window_stats": {
                "recent": {"count": 0, "avg_score": 0.0},
                "learning": {"count": 0, "avg_score": 0.0}
            }
        }
    
    def print_status(self):
        """打印状态"""
        report = self.get_feedback_report()
        config = report["config"]
        system_state = report["system_state"]
        component_analysis = report["component_analysis"]
        stats = report["stats"]
        
        print(f"   📊 闭环反馈系统状态:")
        print(f"      配置:")
        print(f"        权重:")
        print(f"          验证反馈: {config['weights']['validation']:.2f}")
        print(f"          执行反馈: {config['weights']['execution']:.2f}")
        print(f"          结果反馈: {config['weights']['outcome']:.2f}")
        
        print(f"        时间窗口:")
        print(f"          反馈窗口: {config['time_windows']['feedback_window_hours']}小时")
        print(f"          学习窗口: {config['time_windows']['learning_window_hours']}小时")
        
        print(f"      系统状态:")
        print(f"        信念强度: {system_state['belief_strength']:.3f}")
        print(f"        学习效率: {system_state['learning_efficiency']:.3f}")
        print(f"        适应速度: {system_state['adaptation_speed']:.3f}")
        print(f"        稳定性指数: {system_state['stability_index']:.3f}")
        print(f"        重规划频率: {system_state['replan_frequency']:.3f}")
        print(f"        反馈质量: {system_state['feedback_quality']:.3f}")
        
        print(f"      组件分析:")
        for component, analysis in component_analysis.items():
            print(f"        {component}:")
            print(f"          分数: {analysis['score']:.3f}")
            print(f"          权重: {analysis['weight']:.2f}")
            print(f"          贡献: {analysis['contribution']:.1%}")
        
        print(f"      统计:")
        print(f"        总反馈数: {stats['stats']['total_feedbacks']}")
        print(f"        平均反馈分数: {stats['stats']['avg_feedback_score']:.3f}")
        print(f"        重规划次数: {stats['stats']['replan_count']}")
        print(f"        重规划率: {stats['stats']['replan_rate']:.1%}")
        print(f"        反馈趋势: {stats['stats']['feedback_trend']}")
        
        print(f"      时间窗口统计:")
        for window, window_stats in stats['stats']['time_window_stats'].items():
            print(f"        {window}: {window_stats['count']}条目, 平均分数: {window_stats['avg_score']:.3f}")
        
        print(f"      建议:")
        for rec in report.get('recommendations', [])[:3]:
            print(f"        • {rec}")