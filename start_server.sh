#!/bin/bash
# GoldMiner 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置环境变量
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"
export PORT="${PORT:-8888}"
export FLASK_DEBUG="${FLASK_DEBUG:-false}"

echo "🚀 启动 GoldMiner 服务..."
echo "📁 项目目录: ${SCRIPT_DIR}"
echo "🌐 服务端口: ${PORT}"
echo ""

# 进入 ui 目录并启动
cd "${SCRIPT_DIR}/ui" || exit 1
python app.py
