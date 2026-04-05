#!/bin/bash
# 添加OpenClaw cron任务

set -e

echo "添加OpenClaw cron任务..."

# 检查openclaw命令
if ! command -v openclaw &> /dev/null; then
    echo "错误: openclaw命令未找到"
    exit 1
fi

# 添加cron任务
echo "正在添加冥思记忆系统定时任务..."
openclaw cron add --file openclaw_cron_config.json

if [ $? -eq 0 ]; then
    echo "✅ OpenClaw cron任务添加成功"
    
    # 显示任务列表
    echo ""
    echo "当前OpenClaw cron任务:"
    openclaw cron list
    
    echo ""
    echo "任务将在每天凌晨2点（北京时间）自动执行"
    echo "执行结果将发送到Telegram: 5273762787"
else
    echo "❌ OpenClaw cron任务添加失败"
    exit 1
fi
