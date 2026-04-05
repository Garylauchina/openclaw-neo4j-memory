#!/bin/bash
# AI冥思记忆系统 v2.0 部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查Docker
check_docker() {
    log_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    docker_compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    
    log_success "Docker版本: $docker_version"
    log_success "Docker Compose版本: $docker_compose_version"
}

# 检查端口占用
check_ports() {
    log_info "检查端口占用..."
    local ports=("8080" "6379" "5432" "9090" "3000")
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            log_warning "端口 $port 已被占用"
        else
            log_success "端口 $port 可用"
        fi
    done
}

# 准备部署目录
prepare_directories() {
    log_info "准备部署目录..."
    
    # 创建必要的目录
    mkdir -p models state results logs
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    # 设置权限
    chmod -R 755 models state results logs
    chmod -R 755 monitoring
    
    log_success "部署目录准备完成"
}

# 复制应用程序文件
copy_application_files() {
    log_info "复制应用程序文件..."
    
    # 从工作目录复制核心文件
    cp ../gnn_meditation_rule.py .
    cp ../gnn_meditation_model.pth models/
    cp ../meditation_engine_with_gnn_fixed.py .
    cp ../spatial_partition_tree.py .
    cp ../locality_sensitive_hashing.py .
    cp ../incremental_processing.py .
    cp ../meditation_self_integration.py .
    cp ../meditation_state.json state/
    cp ../requirements_meditation_enhanced.txt .
    
    # 创建服务文件
    create_service_files
    
    log_success "应用程序文件复制完成"
}

# 创建服务文件
create_service_files() {
    log_info "创建服务文件..."
    
    # 创建主服务文件
    cat > meditation_service.py << 'SERVICE_EOF'
#!/usr/bin/env python3
"""
冥思记忆系统 - 主服务
提供REST API和Web界面
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
from meditation_self_integration import SelfImprovementIntegration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 全局变量
memory_graph = None
meditation_engine = None
integration = None

def init_system():
    """初始化系统"""
    global memory_graph, meditation_engine, integration
    
    try:
        # 初始化记忆图
        memory_graph = MemoryGraph()
        
        # 初始化冥思引擎
        meditation_engine = MeditationEngine(memory_graph)
        
        # 初始化集成器
        integration = SelfImprovementIntegration()
        
        logger.info("系统初始化完成")
        return True
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        return False

# API路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'v2.0'
    })

@app.route('/api/graph/status', methods=['GET'])
def graph_status():
    """获取图状态"""
    if not memory_graph:
        return jsonify({'error': '系统未初始化'}), 500
    
    try:
        stats = {
            'node_count': len(memory_graph.nodes),
            'edge_count': len(memory_graph.edges),
            'last_updated': datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meditation/run', methods=['POST'])
def run_meditation():
    """运行冥思"""
    if not meditation_engine:
        return jsonify({'error': '冥思引擎未初始化'}), 500
    
    try:
        # 获取参数
        data = request.get_json() or {}
        use_gnn = data.get('use_gnn', True)
        incremental = data.get('incremental', True)
        
        # 运行冥思
        if use_gnn:
            result = meditation_engine.apply_gnn_meditation_rule()
        else:
            result = meditation_engine.run_complete_meditation_workflow()
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/integration/sync', methods=['POST'])
def sync_memories():
    """同步self-improving记忆"""
    if not integration:
        return jsonify({'error': '集成器未初始化'}), 500
    
    try:
        result = integration.sync_memories_to_meditation()
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def config_management():
    """配置管理"""
    config_file = '/data/state/config.json'
    
    if request.method == 'GET':
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    'meditation_frequency': 'daily',
                    'use_gnn': True,
                    'incremental_mode': True,
                    'similarity_threshold': 0.75,
                    'cleanup_threshold': 0.1,
                    'decay_rate': 0.01
                }
            return jsonify(config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            config = request.get_json()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 初始化系统
    if init_system():
        logger.info("启动冥思记忆系统服务...")
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        logger.error("系统初始化失败，服务无法启动")
SERVICE_EOF

    # 创建定时任务服务
    cat > scheduler_service.py << 'SCHEDULER_EOF'
#!/usr/bin/env python3
"""
冥思记忆系统 - 定时任务服务
每天自动运行冥思优化
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/meditation/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_daily_meditation():
    """运行每日冥思"""
    logger.info("开始每日冥思任务...")
    
    try:
        # 运行冥思引擎
        result = subprocess.run([
            'python', 'meditation_engine_with_gnn_fixed.py',
            '--mode', 'daily',
            '--use-gnn',
            '--incremental'
        ], capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            logger.info("每日冥思任务完成")
            logger.info(f"输出: {result.stdout[:500]}...")
        else:
            logger.error(f"每日冥思任务失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("每日冥思任务超时")
    except Exception as e:
        logger.error(f"每日冥思任务异常: {e}")

def run_self_improving_sync():
    """运行self-improving同步"""
    logger.info("开始self-improving同步任务...")
    
    try:
        result = subprocess.run([
            'python', 'meditation_self_integration.py',
            '--sync'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info("self-improving同步任务完成")
        else:
            logger.error(f"self-improving同步任务失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("self-improving同步任务超时")
    except Exception as e:
        logger.error(f"self-improving同步任务异常: {e}")

def run_health_check():
    """运行健康检查"""
    logger.info("运行健康检查...")
    
    try:
        # 检查服务状态
        result = subprocess.run([
            'curl', '-s', 'http://meditation-service:8080/api/health'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info("健康检查通过")
        else:
            logger.error(f"健康检查失败: {result.stderr}")
            
    except Exception as e:
        logger.error(f"健康检查异常: {e}")

def main():
    """主函数"""
    logger.info("启动冥思记忆系统定时任务服务")
    
    # 创建日志目录
    os.makedirs('/var/log/meditation', exist_ok=True)
    
    # 设置定时任务
    # 每天凌晨2点运行冥思
    schedule.every().day.at("02:00").do(run_daily_meditation)
    
    # 每天凌晨3点运行同步
    schedule.every().day.at("03:00").do(run_self_improving_sync)
    
    # 每小时运行健康检查
    schedule.every().hour.do(run_health_check)
    
    logger.info("定时任务设置完成:")
    logger.info("  - 每日冥思: 02:00")
    logger.info("  - 同步任务: 03:00")
    logger.info("  - 健康检查: 每小时")
    
    # 运行一次初始健康检查
    run_health_check()
    
    # 主循环
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("收到停止信号，退出定时任务服务")
            break
        except Exception as e:
            logger.error(f"定时任务服务异常: {e}")
            time.sleep(300)  # 异常后等待5分钟

if __name__ == '__main__':
    main()
SCHEDULER_EOF

    # 创建监控配置文件
    cat > monitoring/prometheus.yml << 'PROMETHEUS_EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'meditation-service'
    static_configs:
      - targets: ['meditation-service:8080']
    metrics_path: '/api/metrics'

  - job_name: 'scheduler'
    static_configs:
      - targets: ['scheduler:8081']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
PROMETHEUS_EOF

    log_success "服务文件创建完成"
}

# 构建Docker镜像
build_docker_images() {
    log_info "构建Docker镜像..."
    
    # 构建主镜像
    docker build -t meditation-memory-system:v2.0 .
    
    if [ $? -eq 0 ]; then
        log_success "Docker镜像构建成功: meditation-memory-system:v2.0"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动Docker Compose服务
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log_success "服务启动成功"
        
        # 显示服务状态
        sleep 5
        docker-compose ps
        
        # 显示访问信息
        show_access_info
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "================================================"
    echo "        AI冥思记忆系统 v2.0 部署完成"
    echo "================================================"
    echo ""
    echo "📊 服务访问信息："
    echo "  • 主服务:      http://localhost:8080"
    echo "  • 监控面板:    http://localhost:3000 (admin/admin)"
    echo "  • Prometheus:  http://localhost:9090"
    echo "  • Redis:       localhost:6379"
    echo "  • PostgreSQL:  localhost:5432"
    echo ""
    echo "🔧 管理命令："
    echo "  • 查看日志:    docker-compose logs -f"
    echo "  • 停止服务:    docker-compose down"
    echo "  • 重启服务:    docker-compose restart"
    echo "  • 更新服务:    ./deploy.sh update"
    echo ""
    echo "📋 定时任务："
    echo "  • 每日冥思:    02:00"
    echo "  • 同步任务:    03:00"
    echo "  • 健康检查:    每小时"
    echo ""
    echo "================================================"
}

# 更新服务
update_services() {
    log_info "更新服务..."
    
    # 停止旧服务
    docker-compose down
    
    # 重新构建镜像
    build_docker_images
    
    # 启动新服务
    start_services
}

# 主函数
main() {
    echo ""
    echo "================================================"
    echo "   AI冥思记忆系统 v2.0 生产环境部署"
    echo "================================================"
    echo ""
    
    # 检查参数
    if [ "$1" = "update" ]; then
        update_services
        exit 0
    fi
    
    # 执行部署步骤
    check_docker
    check_ports
    prepare_directories
    copy_application_files
    build_docker_images
    start_services
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"
