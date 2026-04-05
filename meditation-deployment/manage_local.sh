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
