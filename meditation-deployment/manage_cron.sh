#!/bin/bash
# 冥思记忆系统定时任务管理脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# 显示帮助
show_help() {
    echo "冥思记忆系统定时任务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status     显示定时任务状态"
    echo "  start      启动定时任务服务"
    echo "  stop       停止定时任务服务"
    echo "  restart    重启定时任务服务"
    echo "  logs       查看定时任务日志"
    echo "  test       测试定时任务执行"
    echo "  config     显示定时任务配置"
    echo "  help       显示此帮助信息"
    echo ""
}

# 检查Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose未安装"
        exit 1
    fi
}

# 显示状态
show_status() {
    log "显示定时任务状态..."
    
    # 检查scheduler服务状态
    if docker-compose ps scheduler | grep -q "Up"; then
        success "定时任务服务运行中"
    else
        warning "定时任务服务未运行"
    fi
    
    # 显示定时任务配置
    echo ""
    log "定时任务配置:"
    cat cron_config.json | jq '.schedules | to_entries[] | "  \(.key): \(.value.description) (\(.value.cron_expression))"' 2>/dev/null || cat cron_config.json | grep -A2 -B2 "description"
    
    # 显示最近执行日志
    echo ""
    log "最近执行日志:"
    docker-compose logs scheduler --tail=20 2>/dev/null || echo "  无日志信息"
}

# 启动服务
start_service() {
    log "启动定时任务服务..."
    
    check_docker_compose
    
    # 启动scheduler服务
    docker-compose up -d scheduler
    
    if [ $? -eq 0 ]; then
        success "定时任务服务启动成功"
        
        # 等待服务启动
        sleep 3
        
        # 显示状态
        docker-compose ps scheduler
        
        # 显示日志
        echo ""
        log "服务启动日志:"
        docker-compose logs scheduler --tail=10
    else
        error "定时任务服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log "停止定时任务服务..."
    
    check_docker_compose
    
    docker-compose stop scheduler
    
    if [ $? -eq 0 ]; then
        success "定时任务服务停止成功"
    else
        error "定时任务服务停止失败"
        exit 1
    fi
}

# 重启服务
restart_service() {
    log "重启定时任务服务..."
    
    stop_service
    start_service
}

# 查看日志
show_logs() {
    log "查看定时任务日志..."
    
    check_docker_compose
    
    if [ "$1" = "-f" ]; then
        # 实时查看日志
        docker-compose logs -f scheduler
    else
        # 查看最近日志
        docker-compose logs scheduler --tail=50
    fi
}

# 测试任务执行
test_tasks() {
    log "测试定时任务执行..."
    
    echo ""
    log "测试每日冥思任务..."
    docker-compose exec scheduler python -c "
import subprocess
import sys

try:
    result = subprocess.run([
        'python', 'meditation_engine_with_gnn_fixed.py',
        '--mode', 'test',
        '--use-gnn',
        '--incremental'
    ], capture_output=True, text=True, timeout=300)
    
    if result.returncode == 0:
        print('✓ 每日冥思任务测试通过')
        print(f'输出: {result.stdout[:200]}...')
    else:
        print('✗ 每日冥思任务测试失败')
        print(f'错误: {result.stderr}')
        
except subprocess.TimeoutExpired:
    print('✗ 每日冥思任务测试超时')
except Exception as e:
    print(f'✗ 每日冥思任务测试异常: {e}')
"
    
    echo ""
    log "测试self-improving同步任务..."
    docker-compose exec scheduler python -c "
import subprocess
import sys

try:
    result = subprocess.run([
        'python', 'meditation_self_integration.py',
        '--test'
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        print('✓ 同步任务测试通过')
        print(f'输出: {result.stdout[:200]}...')
    else:
        print('✗ 同步任务测试失败')
        print(f'错误: {result.stderr}')
        
except subprocess.TimeoutExpired:
    print('✗ 同步任务测试超时')
except Exception as e:
    print(f'✗ 同步任务测试异常: {e}')
"
    
    echo ""
    log "测试健康检查..."
    docker-compose exec scheduler curl -s http://meditation-service:8080/api/health
    
    if [ $? -eq 0 ]; then
        success "健康检查测试通过"
    else
        error "健康检查测试失败"
    fi
}

# 显示配置
show_config() {
    log "显示定时任务配置..."
    
    echo ""
    log "完整配置:"
    cat cron_config.json | jq '.' 2>/dev/null || cat cron_config.json
    
    echo ""
    log "OpenClaw cron配置:"
    cat openclaw_cron_config.json | jq '.' 2>/dev/null || cat openclaw_cron_config.json
    
    echo ""
    log "Docker Compose配置:"
    docker-compose config 2>/dev/null || echo "无法获取Docker Compose配置"
}

# 主函数
main() {
    case "$1" in
        status)
            show_status
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        logs)
            show_logs "$2"
            ;;
        test)
            test_tasks
            ;;
        config)
            show_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                show_status
            else
                error "未知命令: $1"
                show_help
                exit 1
            fi
            ;;
    esac
}

# 执行主函数
main "$@"
