#!/bin/bash
# 监控系统设置脚本

set -e

echo "设置监控系统..."

# 创建Alertmanager配置
cat > monitoring/alertmanager.yml << 'ALERTMANAGER_EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://telegram-bot:8080/alerts'

  - name: 'critical'
    webhook_configs:
      - url: 'http://telegram-bot:8080/critical'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'

  - name: 'warning'
    webhook_configs:
      - url: 'http://telegram-bot:8080/warning'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
ALERTMANAGER_EOF

echo "✅ Alertmanager配置已创建"

# 创建Prometheus数据源配置
cat > monitoring/grafana/datasources/prometheus.yml << 'DATASOURCE_EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
DATASOURCE_EOF

echo "✅ Prometheus数据源配置已创建"

# 创建Telegram通知脚本
cat > monitoring/telegram_notifier.py << 'TELEGRAM_EOF'
#!/usr/bin/env python3
"""
Telegram告警通知服务
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5273762787')

# 创建Flask应用
app = Flask(__name__)

def send_telegram_alert(alert):
    """发送Telegram告警"""
    import requests
    
    try:
        message = f"""
🚨 <b>{alert['labels']['severity'].upper()}</b> - {alert['annotations']['summary']}

📝 <b>详情：</b>
{alert['annotations']['description']}

🏷️ <b>标签：</b>
{json.dumps(alert['labels'], indent=2)}

⏰ <b>时间：</b>
{alert['startsAt']}
"""
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        logger.info(f"告警已发送: {alert['annotations']['summary']}")
        return True
        
    except Exception as e:
        logger.error(f"发送Telegram告警失败: {e}")
        return False

@app.route('/alerts', methods=['POST'])
def receive_alerts():
    """接收Alertmanager告警"""
    alerts = request.json
    
    for alert in alerts.get('alerts', []):
        send_telegram_alert(alert)
    
    return jsonify({'status': 'success'}), 200

@app.route('/critical', methods=['POST'])
def receive_critical():
    """接收严重告警"""
    alerts = request.json
    
    for alert in alerts.get('alerts', []):
        if alert.get('labels', {}).get('severity') == 'critical':
            send_telegram_alert(alert)
    
    return jsonify({'status': 'success'}), 200

@app.route('/warning', methods=['POST'])
def receive_warning():
    """接收警告"""
    alerts = request.json
    
    for alert in alerts.get('alerts', []):
        if alert.get('labels', {}).get('severity') == 'warning':
            send_telegram_alert(alert)
    
    return jsonify({'status': 'success'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("启动Telegram告警通知服务...")
    app.run(host='0.0.0.0', port=8080, debug=False)
TELEGRAM_EOF

chmod +x monitoring/telegram_notifier.py

echo "✅ Telegram通知服务已创建"

echo "✅ 监控系统设置完成"
