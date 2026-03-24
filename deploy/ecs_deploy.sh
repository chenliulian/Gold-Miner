#!/bin/bash
# GoldMiner ECS 部署脚本
# 用法: ./deploy/ecs_deploy.sh

set -e

echo "🚀 开始部署 GoldMiner 到阿里云 ECS..."

# 配置变量
APP_NAME="goldminer"
APP_DIR="/opt/goldminer"
APP_USER="goldminer"
PYTHON_VERSION="3.11"
PORT="8888"

# 1. 安装系统依赖
echo "📦 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    git \
    nginx \
    supervisor \
    build-essential \
    libssl-dev

# 2. 创建应用用户
echo "👤 创建应用用户..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -d $APP_DIR $APP_USER
fi

# 3. 创建应用目录
echo "📁 创建应用目录..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# 4. 克隆代码（或复制本地代码）
echo "📥 部署代码..."
# 方式1: 从 Git 拉取
# sudo -u $APP_USER git clone https://github.com/chenliulian/Gold-Miner.git $APP_DIR

# 方式2: 从本地复制（推荐，先压缩再上传）
# tar czf goldminer.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' .
# scp goldminer.tar.gz root@your-ecs-ip:/tmp/
# sudo -u $APP_USER tar xzf /tmp/goldminer.tar.gz -C $APP_DIR --strip-components=1

echo "⚠️  请手动将代码复制到 $APP_DIR 目录"
echo "   示例: scp -r . root@your-ecs-ip:$APP_DIR"

# 5. 创建 Python 虚拟环境
echo "🐍 创建虚拟环境..."
sudo -u $APP_USER bash -c "cd $APP_DIR && python${PYTHON_VERSION} -m venv venv"

# 6. 安装依赖
echo "📚 安装 Python 依赖..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && pip install -e ."

# 7. 创建环境变量文件
echo "⚙️  配置环境变量..."
sudo -u $APP_USER bash -c "cat > $APP_DIR/.env << 'EOF'
# 从本地 .env 文件复制所有配置
# 确保修改以下配置：
# - LLM_BASE_URL
# - LLM_API_KEY
# - ODPS_ACCESS_ID
# - ODPS_ACCESS_KEY
# - SESSION_SECRET

PORT=$PORT
FLASK_DEBUG=false
EOF"

echo "⚠️  请手动编辑 $APP_DIR/.env 文件，填入实际配置"

# 8. 创建日志目录
echo "📝 创建日志目录..."
sudo mkdir -p /var/log/goldminer
sudo chown $APP_USER:$APP_USER /var/log/goldminer

echo "✅ 基础部署完成！"
echo ""
echo "下一步:"
echo "  1. 复制代码到 $APP_DIR"
echo "  2. 编辑 $APP_DIR/.env 配置"
echo "  3. 运行 ./deploy/ecs_setup_service.sh 配置服务"
