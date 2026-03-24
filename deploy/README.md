# GoldMiner ECS 部署指南

## 1. 准备 ECS 服务器

### 推荐配置
- **系统**: Ubuntu 22.04 LTS
- **CPU**: 2核+
- **内存**: 4GB+
- **带宽**: 5Mbps+
- **安全组**: 开放 80 端口

### 购买后操作
1. 创建 ECS 实例
2. 配置安全组，允许 80 端口入站
3. 绑定弹性公网 IP
4. 记录公网 IP 地址

---

## 2. 本地准备

### 打包代码
```bash
cd GoldMiner
# 排除不必要的文件，打包代码
tar czf goldminer-deploy.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='.env' \
  --exclude='*.log' \
  --exclude='reports/*' \
  --exclude='memory/*' \
  --exclude='ui/sessions/*' \
  .
```

### 准备环境变量文件
复制 `.env` 文件并命名为 `.env.production`，修改以下配置：
```bash
# 生产环境配置
PORT=8888
FLASK_DEBUG=false

# 确保所有 API 密钥和数据库配置正确
# LLM_BASE_URL=
# LLM_API_KEY=
# ODPS_ACCESS_ID=
# ODPS_ACCESS_KEY=
# SESSION_SECRET=  # 必须设置！
```

---

## 3. 上传到 ECS

```bash
# 上传代码包
scp goldminer-deploy.tar.gz root@your-ecs-ip:/tmp/

# 上传环境变量文件
scp .env.production root@your-ecs-ip:/tmp/.env

# SSH 登录
ssh root@your-ecs-ip
```

---

## 4. 在 ECS 上部署

### 4.1 解压代码
```bash
cd /tmp
tar xzf goldminer-deploy.tar.gz -C /opt/
mv /opt/GoldMiner /opt/goldminer
mv /tmp/.env /opt/goldminer/.env
```

### 4.2 运行部署脚本
```bash
cd /opt/goldminer

# 1. 安装依赖
chmod +x deploy/ecs_deploy.sh
./deploy/ecs_deploy.sh

# 2. 配置服务（需要 sudo）
chmod +x deploy/ecs_setup_service.sh
sudo ./deploy/ecs_setup_service.sh
```

### 4.3 手动步骤
部署脚本会提示你完成以下手动操作：

1. **编辑环境变量**
   ```bash
   sudo nano /opt/goldminer/.env
   # 填入所有必要的 API 密钥和配置
   ```

2. **安装依赖**（如果脚本未完成）
   ```bash
   cd /opt/goldminer
   sudo -u goldminer bash -c "source venv/bin/activate && pip install -e ."
   ```

---

## 5. 启动服务

```bash
# 启动 GoldMiner
sudo supervisorctl start goldminer

# 查看状态
sudo supervisorctl status goldminer

# 查看日志
sudo tail -f /var/log/goldminer/error.log
sudo tail -f /var/log/goldminer/access.log
```

---

## 6. 访问应用

浏览器访问：
```
http://your-ecs-ip
```

---

## 7. 常用运维命令

### 重启服务
```bash
sudo supervisorctl restart goldminer
```

### 停止服务
```bash
sudo supervisorctl stop goldminer
```

### 更新代码后
```bash
cd /opt/goldminer
sudo -u goldminer git pull origin main  # 如果用 git
# 或重新上传代码

sudo supervisorctl restart goldminer
```

### 查看 Nginx 日志
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 8. 配置域名（可选）

### 8.1 域名解析
在阿里云域名控制台添加 A 记录：
- 主机记录: `goldminer`
- 记录值: `your-ecs-ip`

### 8.2 修改 Nginx 配置
```bash
sudo nano /etc/nginx/sites-available/goldminer
```

修改 `server_name`:
```nginx
server {
    listen 80;
    server_name goldminer.yourdomain.com;
    ...
}
```

### 8.3 配置 HTTPS（推荐）
```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d goldminer.yourdomain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 9. 安全建议

1. **修改默认端口**: 将 SSH 端口从 22 改为其他端口
2. **配置防火墙**: 只开放 80/443 端口
3. **定期备份**: 备份 `.env` 文件和数据库
4. **监控日志**: 定期检查访问日志和错误日志

---

## 10. 故障排查

### 服务无法启动
```bash
# 检查 Python 依赖
sudo -u goldminer bash -c "cd /opt/goldminer && source venv/bin/activate && python ui/app.py"

# 查看详细错误
sudo tail -f /var/log/goldminer/error.log
```

### 端口被占用
```bash
# 查看端口占用
sudo lsof -i :8888

# 结束进程
sudo kill -9 <PID>
```

### Nginx 502 错误
```bash
# 检查 GoldMiner 是否运行
sudo supervisorctl status goldminer

# 检查端口监听
sudo netstat -tlnp | grep 8888
```
