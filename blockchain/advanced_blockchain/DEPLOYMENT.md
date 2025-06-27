# 区块链系统部署指南

## 📋 部署概述

本指南将帮助您在不同环境中部署高级区块链系统，支持单节点和多节点分布式部署。

## 🚀 快速部署

### 1. 环境准备

```bash
# 系统要求
- Python 3.8+
- 内存: 512MB+ (建议1GB+)
- 存储: 1GB+ 可用空间
- 网络: 稳定的网络连接

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 单节点部署

```bash
# 基础节点
python scripts/start_node.py

# 自动挖矿节点
python scripts/start_node.py --auto-mine --difficulty 3

# 指定端口
python scripts/start_node.py --port 5001 --host 0.0.0.0
```

### 3. 多节点网络部署

```bash
# 主节点 (服务器1)
python scripts/start_node.py --port 5000 --host 0.0.0.0 --auto-mine

# 从节点 (服务器2)
python scripts/start_node.py --port 5000 --host 0.0.0.0 --peers 主节点IP:5000

# 从节点 (服务器3)
python scripts/start_node.py --port 5000 --host 0.0.0.0 --peers 主节点IP:5000,服务器2IP:5000
```

## 🐳 Docker部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "scripts/start_node.py", "--host", "0.0.0.0"]
```

### 2. 构建和运行

```bash
# 构建镜像
docker build -t advanced-blockchain .

# 运行单节点
docker run -p 5000:5000 advanced-blockchain

# 运行多节点网络
docker run -p 5000:5000 advanced-blockchain --auto-mine
docker run -p 5001:5000 advanced-blockchain --peers blockchain-node1:5000
```

### 3. Docker Compose部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  blockchain-node1:
    build: .
    ports:
      - "5000:5000"
    command: ["python", "scripts/start_node.py", "--host", "0.0.0.0", "--auto-mine"]
    volumes:
      - blockchain1_data:/app/data

  blockchain-node2:
    build: .
    ports:
      - "5001:5000"
    depends_on:
      - blockchain-node1
    command: ["python", "scripts/start_node.py", "--host", "0.0.0.0", "--peers", "blockchain-node1:5000"]
    volumes:
      - blockchain2_data:/app/data

volumes:
  blockchain1_data:
  blockchain2_data:
```

```bash
# 启动网络
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止网络
docker-compose down
```

## ☁️ 云服务器部署

### AWS EC2部署

1. **创建EC2实例**
   - 选择Ubuntu 20.04 LTS
   - 实例类型: t3.medium (推荐)
   - 安全组开放端口: 5000, 22

2. **安装依赖**
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

3. **部署应用**
```bash
git clone <your-repo>
cd blockchain/advanced_blockchain
pip3 install -r requirements.txt
python3 scripts/start_node.py --host 0.0.0.0 --auto-mine
```

### 阿里云ECS部署

1. **创建ECS实例**
   - 镜像: CentOS 8 或 Ubuntu 20.04
   - 实例规格: 2核4GB (推荐)
   - 安全组规则: 开放5000端口

2. **安装环境**
```bash
# CentOS
sudo yum update -y
sudo yum install python3 python3-pip git -y

# Ubuntu
sudo apt update
sudo apt install python3 python3-pip git -y
```

3. **系统服务配置**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/blockchain.service

[Unit]
Description=Advanced Blockchain Node
After=network.target

[Service]
Type=simple
User=blockchain
WorkingDirectory=/home/blockchain/advanced_blockchain
ExecStart=/usr/bin/python3 scripts/start_node.py --host 0.0.0.0 --auto-mine
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl enable blockchain
sudo systemctl start blockchain
sudo systemctl status blockchain
```

## 🔧 生产环境配置

### 1. 反向代理配置 (Nginx)

```nginx
# /etc/nginx/sites-available/blockchain
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. SSL证书配置

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 5000
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

## 📊 监控和日志

### 1. 系统监控

```bash
# 安装监控工具
pip install psutil prometheus-client

# 创建监控脚本
# scripts/monitor.py
import psutil
import time
import requests

def monitor_system():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"CPU: {cpu_percent}%")
        print(f"内存: {memory.percent}%")
        print(f"磁盘: {disk.percent}%")
        
        # 检查节点状态
        try:
            response = requests.get("http://localhost:5000/api/v1/status")
            print(f"节点状态: {response.status_code}")
        except:
            print("节点状态: 离线")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_system()
```

### 2. 日志管理

```bash
# 配置日志轮转
sudo vim /etc/logrotate.d/blockchain

/var/log/blockchain/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

## 🔐 安全配置

### 1. 网络安全

```bash
# 限制API访问
# 在config/settings.py中配置
ALLOWED_HOSTS = ["trusted-ip-1", "trusted-ip-2"]

# 使用API密钥认证
API_KEY_REQUIRED = True
VALID_API_KEYS = ["your-secret-api-key"]
```

### 2. 钱包安全

```bash
# 加密钱包文件
gpg --symmetric --cipher-algo AES256 wallets/miner.json

# 设置文件权限
chmod 600 wallets/*.json
chown blockchain:blockchain wallets/*.json
```

### 3. 系统安全

```bash
# 创建专用用户
sudo adduser blockchain
sudo usermod -aG sudo blockchain

# 禁用root登录
sudo vim /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no

# 重启SSH服务
sudo systemctl restart ssh
```

## 📈 性能优化

### 1. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.rmem_max = 134217728" >> /etc/sysctl.conf
echo "net.core.wmem_max = 134217728" >> /etc/sysctl.conf
sysctl -p
```

### 2. 应用优化

```python
# config/production.py
MINING_DIFFICULTY = 4
MAX_TRANSACTIONS_PER_BLOCK = 1000
TRANSACTION_POOL_SIZE = 50000
SYNC_INTERVAL = 5
```

## 🚨 故障排除

### 常见问题

1. **端口被占用**
```bash
# 查看端口使用情况
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000

# 杀死进程
sudo kill -9 <PID>
```

2. **内存不足**
```bash
# 添加swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

3. **节点同步失败**
```bash
# 检查网络连接
ping <peer-ip>
telnet <peer-ip> 5000

# 检查防火墙
sudo ufw status
sudo iptables -L
```

## 📞 技术支持

如果遇到部署问题，请：

1. 检查系统日志: `sudo journalctl -u blockchain`
2. 查看应用日志: `tail -f logs/blockchain.log`
3. 验证配置文件: `python -c "import config.settings"`
4. 联系技术支持

---

**🎯 部署完成后，访问 `http://your-server:5000/api/v1/status` 验证系统运行状态！** 