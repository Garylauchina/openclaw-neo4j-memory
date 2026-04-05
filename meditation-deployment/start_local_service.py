#!/usr/bin/env python3
"""
冥思记忆系统 - 本地服务启动脚本
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import json
import schedule
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/local_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_meditation():
    """运行冥思优化"""
    logger.info("开始执行冥思优化...")
    
    try:
        from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
        from meditation_self_integration import SelfImprovementIntegration
        
        # 初始化系统
        graph = MemoryGraph()
        engine = MeditationEngine(graph)
        integration = SelfImprovementIntegration()
        
        # 同步记忆
        logger.info("同步self-improving记忆...")
        sync_result = integration.sync_memories_to_meditation()
        
        # 将同步的节点添加到图中
        if 'sync_result' in sync_result and 'nodes' in sync_result['sync_result']:
            for node_data in sync_result['sync_result']['nodes']:
                graph.add_node(node_data)
            
            # 添加边
            if 'edges' in sync_result['sync_result']:
                for edge_data in sync_result['sync_result']['edges']:
                    graph.add_edge(edge_data)
            
            logger.info(f"已加载 {len(sync_result['sync_result']['nodes'])} 个节点和 {len(sync_result['sync_result']['edges'])} 条边到图中")
        
        # 运行冥思
        logger.info("运行冥思优化...")
        meditation_result = engine.run_meditation()
        
        logger.info(f"冥思优化完成")
        logger.info(f"  同步: {sync_result.get('new_nodes_count', 0)} 个节点")
        logger.info(f"  优化: {meditation_result.get('total_nodes_processed', 0)} 个节点")
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f'results/meditation_result_{timestamp}.json'
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'sync_result': sync_result,
                'meditation_result': meditation_result,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"结果已保存: {result_file}")
        return True
        
    except Exception as e:
        logger.error(f"冥思优化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        logger.error(f"冥思优化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_health_check():
    """运行健康检查"""
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '-c', 'from meditation_engine_with_gnn_fixed import MemoryGraph; graph = MemoryGraph(); print("OK")'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            logger.info("健康检查通过")
        else:
            logger.warning(f"健康检查异常: {result.stderr}")
            
    except Exception as e:
        logger.error(f"健康检查失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='冥思记忆系统本地服务')
    parser.add_argument('--mode', choices=['once', 'service', 'schedule'], default='once',
                       help='运行模式: once(一次), service(服务), schedule(定时)')
    parser.add_argument('--schedule', choices=['hourly', 'daily'], default='daily',
                       help='定时模式: hourly(每小时), daily(每天)')
    parser.add_argument('--time', default='02:00', help='定时执行时间')
    
    args = parser.parse_args()
    
    if args.mode == 'once':
        # 单次执行
        logger.info("模式: 单次执行")
        run_meditation()
        
    elif args.mode == 'service':
        # 服务模式（持续运行）
        logger.info("模式: 服务模式")
        logger.info("启动冥思记忆系统服务...")
        
        # 设置定时任务
        if args.schedule == 'daily':
            schedule.every().day.at(args.time).do(run_meditation)
            schedule.every().hour.do(run_health_check)
            logger.info(f"定时设置: 每天 {args.time} 执行冥思，每小时健康检查")
        elif args.schedule == 'hourly':
            schedule.every().hour.do(run_meditation)
            logger.info("定时设置: 每小时执行冥思")
        
        # 立即执行一次健康检查
        run_health_check()
        
        # 主循环
        logger.info("服务已启动，等待定时任务...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("收到停止信号，服务退出")
                break
            except Exception as e:
                logger.error(f"服务异常: {e}")
                time.sleep(60)
                
    elif args.mode == 'schedule':
        # 定时模式
        logger.info(f"模式: 定时模式 ({args.schedule})")
        
        if args.schedule == 'daily':
            schedule.every().day.at(args.time).do(run_meditation)
            logger.info(f"定时设置: 每天 {args.time} 执行冥思")
        elif args.schedule == 'hourly':
            schedule.every().hour.do(run_meditation)
            logger.info("定时设置: 每小时执行冥思")
        
        # 等待并执行
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("收到停止信号，退出")
                break
            except Exception as e:
                logger.error(f"执行异常: {e}")
                time.sleep(60)

if __name__ == '__main__':
    main()
