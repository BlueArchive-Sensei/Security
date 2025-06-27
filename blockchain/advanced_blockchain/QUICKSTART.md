# 🚀 快速开始指南

## 📋 一分钟体验

### 1. 安装依赖
```bash
cd blockchain/advanced_blockchain
pip install -r requirements.txt
```

### 2. 运行演示
```bash
python demo_script.py
```

### 3. 启动节点
```bash
python scripts/start_node.py --auto-mine
```

### 4. 测试API
```bash
# 获取节点状态
curl http://localhost:5000/api/v1/status

# 创建钱包
curl -X POST http://localhost:5000/api/v1/wallet/new
```

## 🎯 常用命令

```bash
# 启动基础节点
python scripts/start_node.py

# 启动自动挖矿节点
python scripts/start_node.py --auto-mine

# 启动多端口节点
python scripts/start_node.py --port 5001 --auto-mine

# 连接到其他节点
python scripts/start_node.py --peers localhost:5000

# 创建钱包
python scripts/start_node.py create-wallet --name my_wallet

# 从文件加载区块链
python scripts/start_node.py --load-blockchain backup.json
```

## 📊 API使用示例

### 创建交易
```bash
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "发送者地址",
    "receiver": "接收者地址",
    "amount": 100,
    "fee": 1,
    "private_key": "私钥"
  }'
```

### 查询余额
```bash
curl http://localhost:5000/api/v1/balance/你的地址
```

### 挖矿
```bash
curl -X POST http://localhost:5000/api/v1/mine \
  -H "Content-Type: application/json" \
  -d '{"miner_address": "矿工地址"}'
```

## 🌐 搭建网络

### 三节点网络
```bash
# 终端1 - 主节点
python scripts/start_node.py --port 5000 --auto-mine

# 终端2 - 节点2  
python scripts/start_node.py --port 5001 --peers localhost:5000

# 终端3 - 节点3
python scripts/start_node.py --port 5002 --peers localhost:5000,localhost:5001
```

## 🔧 常见问题

**Q: 端口被占用怎么办？**
```bash
# 查看端口使用
lsof -i :5000
# 或使用不同端口
python scripts/start_node.py --port 5001
```

**Q: 挖矿太慢怎么办？**
```bash
# 降低难度
python scripts/start_node.py --difficulty 2 --auto-mine
```

**Q: 如何重置区块链？**
```bash
# 删除数据文件
rm -rf blockchain_*.json wallets/
```

## 📚 进阶学习

- 📖 [完整文档](README.md)
- 🚀 [部署指南](DEPLOYMENT.md)  
- 🔧 [技术指南](TECHNICAL_GUIDE.md)

---

**⚡ 立即开始你的区块链之旅！** 