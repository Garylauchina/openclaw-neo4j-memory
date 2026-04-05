#!/bin/bash
# AI冥思记忆系统 v2.0 本地部署脚本（非Docker）

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

echo ""
echo "================================================"
echo "   AI冥思记忆系统 v2.0 本地部署"
echo "================================================"
echo ""

# 检查Python环境
log "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

python_version=$(python3 --version | cut -d' ' -f2)
success "Python版本: $python_version"

# 检查虚拟环境
log "检查虚拟环境..."
VENV_PATH="/Users/liugang/.openclaw/venv/meditation-gnn"

if [ ! -d "$VENV_PATH" ]; then
    warning "虚拟环境不存在，创建虚拟环境..."
    python3 -m venv "$VENV_PATH"
else
    success "虚拟环境已存在"
fi

# 激活虚拟环境
log "激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 检查依赖
log "检查依赖安装..."
pip list | grep -q "torch" || {
    warning "依赖未安装，安装依赖..."
    pip install -q --upgrade pip
    pip install -q -r requirements_meditation_enhanced.txt
}

success "依赖已安装"

# 创建数据目录
log "创建数据目录..."
mkdir -p logs state results models

# 测试冥思引擎
log "测试冥思引擎..."
python3 << 'TEST_PYTHON'
try:
    from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
    print("✅ 冥思引擎导入成功")
    
    # 创建测试图
    graph = MemoryGraph()
    print(f"✅ 记忆图创建成功")
    
    # 创建引擎
    engine = MeditationEngine(graph)
    print(f"✅ 冥思引擎创建成功")
    
    print("✅ 本地部署测试通过")
    exit(0)
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
TEST_PYTHON

if [ $? -eq 0 ]; then
    success "冥思引擎测试通过"
else
    echo "❌ 冥思引擎测试失败"
    exit 1
fi

# 创建本地服务启动脚本
cat > start_local_service.py << 'SERVICE_EOF'
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
        
        # 运行冥思
        logger.info("运行冥思优化...")
        if os.path.exists('models/gnn_meditation_model.pth'):
            meditation_result = engine.apply_gnn_meditation_rule()
        else:
            meditation_result = engine.run_complete_meditation_workflow()
        
        logger.info(f"冥思优化完成")
        logger.info(f"  同步: {sync_result.get('new_nodes_count', 0)} 个节点")
        logger.info(f"  优化: {meditation_result.get('nodes_processed', 0)} 个节点")
        
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
SERVICE_EOF

chmod +x start_local_service.py

success "本地服务启动脚本已创建"

# 创建本地服务管理脚本
cat > manage_local.sh << 'MANAGE_EOF'
#!/bin/bash
# 本地服务管理脚本

VENV_PATH="/Users/liugang/.openclaw/venv/meditation-gnn"
DEPLOY_PATH="/Users/liugang/.openclaw/workspace/meditation-deployment"

# 激活虚拟环境
activate_venv() {
    source "$VENV_PATH/bin/activate"
    cd "$DEPLOY_PATH"
}

start() {
    echo "启动冥思记忆系统本地服务..."
    activate_venv
    nohup python3 start_local_service.py --mode service --schedule daily --time 02:00 > logs/service.log 2>&1 &
    echo $! > logs/service.pid
    echo "服务已启动，PID: $(cat logs/service.pid)"
    echo "日志: logs/service.log"
}

stop() {
    echo "停止冥思记忆系统本地服务..."
    if [ -f logs/service.pid ]; then
        pid=$(cat logs/service.pid)
        kill $pid 2>/dev/null
        rm logs/service.pid
        echo "服务已停止"
    else
        echo "服务未运行"
    fi
}

status() {
    echo "冥思记忆系统服务状态:"
    if [ -f logs/service.pid ]; then
        pid=$(cat logs/service.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo "  ✅ 服务运行中 (PID: $pid)"
            echo "  📋 最近日志:"
            tail -20 logs/service.log
        else
            echo "  ❌ 服务已停止 (PID文件存在)"
            rm logs/service.pid
        fi
    else
        echo "  ⏸️  服务未运行"
    fi
}

logs() {
    if [ "$1" = "-f" ]; then
        tail -f logs/service.log
    else
        tail -50 logs/service.log
    fi
}

run() {
    echo "运行一次冥思优化..."
    activate_venv
    python3 start_local_service.py --mode once
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    run)
        run
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|run}"
        exit 1
        ;;
esac
MANAGE_EOF

chmod +x manage_local.sh

success "本地服务管理脚本已创建"

echo ""
echo "================================================"
echo "        本地部署完成"
echo "================================================"
echo ""
echo "🔧 管理命令："
echo "  ./manage_local.sh start    # 启动服务"
echo "  ./manage_local.sh stop     # 停止服务"
echo "  ./manage_local.sh status   # 查看状态"
echo "  ./manage_local.sh logs     # 查看日志"
echo "  ./manage_local.sh run      # 运行一次"
echo ""
echo "📅 定时任务："
echo "  • 每日冥思: 02:00 (北京时间)"
echo "  • 健康检查: 每小时"
echo ""
echo "📁 数据目录："
echo "  • 日志: logs/"
echo "  • 状态: state/"
echo "  • 结果: results/"
echo "  • 模型: models/"
echo ""
echo "================================================"
