#!/bin/bash
# 监控系统管理脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

show_help() {
    cat << 'HELP'
监控系统管理脚本

用法: $0 [命令]

命令:
  status      显示监控状态
  start       启动监控系统
  stop        停止监控系统
  restart     重启监控系统
  logs        查看监控日志
  test        测试告警
  help        显示帮助信息

HELP
}

show_status() {
    log "显示监控系统状态..."
    
    # 检查Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        success "Prometheus: 在线"
    else
        warning "Prometheus: 离线"
    fi
    
    # 检查Grafana
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        success "Grafana: 在线"
    else
        warning "Grafana: 离线"
    fi
    
    # 显示活跃告警
    echo ""
    log "活跃告警:"
    curl -s 'http://localhost:9090/api/v1/alerts' | jq '.[] | select(.state=="firing") | {alertname: .labels.alertname, severity: .labels.severity}' 2>/dev/null || echo "  无活跃告警"
}

start_monitoring() {
    log "启动监控系统..."
    
    # 启动监控相关服务
    docker-compose up -d prometheus grafana
    
    if [ $? -eq 0 ]; then
        success "监控系统启动成功"
        
        # 等待服务启动
        sleep 5
        
        # 显示访问信息
        echo ""
        echo "📊 监控面板访问信息:"
        echo "  • Prometheus:  http://localhost:9090"
        echo "  • Grafana:     http://localhost:3000 (admin/admin)"
        echo ""
    else
        error "监控系统启动失败"
        exit 1
    fi
}

stop_monitoring() {
    log "停止监控系统..."
    
    docker-compose stop prometheus grafana
    
    if [ $? -eq 0 ]; then
        success "监控系统停止成功"
    else
        error "监控系统停止失败"
        exit 1
    fi
}

restart_monitoring() {
    log "重启监控系统..."
    
    stop_monitoring
    sleep 2
    start_monitoring
}

show_logs() {
    log "查看监控日志..."
    
    if [ "$1" = "-f" ]; then
        # 实时查看日志
        docker-compose logs -f prometheus grafana
    else
        # 查看最近日志
        docker-compose logs prometheus grafana --tail=50
    fi
}

test_alerts() {
    log "测试告警系统..."
    
    # 发送测试告警
    curl -X POST http://localhost:8080/alerts \
        -H "Content-Type: application/json" \
        -d '{
            "alerts": [
                {
                    "labels": {
                        "severity": "info",
                        "alertname": "test"
                    },
                    "annotations": {
                        "summary": "测试告警",
                        "description": "这是一个测试告警"
                    },
                    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
                }
            ]
        }'
    
    if [ $? -eq 0 ]; then
        success "测试告警发送成功，请检查Telegram"
    else
        error "测试告警发送失败"
    fi
}

main() {
    case "$1" in
        status)
            show_status
            ;;
        start)
            start_monitoring
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            restart_monitoring
            ;;
        logs)
            show_logs "$2"
            ;;
        test)
            test_alerts
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

main "$@"
