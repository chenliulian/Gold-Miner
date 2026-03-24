#!/bin/bash
# GoldMiner ECS 服务配置脚本
# 用法: sudo ./deploy/ecs_setup_service.sh

set -e

APP_NAME="goldminer"
APP_DIR="/opt/goldminer"
APP_USER="goldminer"
PORT="8888"

echo "🔧 配置 GoldMiner 服务..."

# 1. 创建 Supervisor 配置
echo "📋 配置 Supervisor..."
cat > /etc/supervisor/conf.d/goldminer.conf << EOF
[program:goldminer]
directory=$APP_DIR
command=$APP_DIR/venv/bin/python ui/app.py
user=$APP_USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/goldminer/error.log
stdout_logfile=/var/log/goldminer/access.log
environment=PYTHONPATH="$APP_DIR/src",PORT="$PORT",FLASK_DEBUG="false"
EOF

# 2. 创建 Nginx 配置
echo "🌐 配置 Nginx..."
cat > /etc/nginx/sites-available/goldminer << 'EOF'
server {
    listen 80;
    server_name _;  # 接受所有域名

    client_max_body_size 100M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Cache-Control no-cache;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/goldminer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 3. 测试配置
echo "🧪 测试配置..."
nginx -t

# 4. 启动服务
echo "🚀 启动服务..."
supervisorctl reread
supervisorctl update
supervisorctl start goldminer

systemctl restart nginx
systemctl enable nginx
systemctl enable supervisor

echo "✅ 服务配置完成！"
echo ""
echo "查看状态:"
echo "  supervisorctl status goldminer"
echo "  查看日志: tail -f /var/log/goldminer/error.log"
echo "  Nginx日志: tail -f /var/log/nginx/access.log"
