# 高级区块链系统 - Advanced Blockchain

## 📋 项目简介

这是一个基于Python实现的完整区块链系统，具备现代区块链的核心功能：

- 🔐 **ECDSA数字签名** - 确保交易安全性
- 🌐 **P2P网络通信** - 支持多节点分布式运行
- 🌲 **Merkle树验证** - 高效的数据完整性验证
- 💼 **交易池管理** - 智能的交易优先级处理
- ⚡ **REST API + WebSocket** - 完整的网络接口
- 📊 **实时监控** - 区块链状态和性能监控

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip包管理器

### 安装依赖

```bash
# 进入项目目录
cd blockchain/advanced_blockchain

# 安装依赖
pip install -r requirements.txt
```

### 启动单节点

```bash
# 启动基础节点
python scripts/start_node.py

# 启动自动挖矿节点
python scripts/start_node.py --auto-mine

# 指定端口启动
python scripts/start_node.py --port 5001
```

### 创建钱包

```bash
# 创建新钱包
python scripts/start_node.py create-wallet --name my_wallet
```

## 🏗️ 项目结构

```
advanced_blockchain/
├── src/                    # 源代码
│   ├── core/              # 核心区块链组件
│   │   ├── blockchain.py  # 区块链主类
│   │   ├── block.py       # 区块类
│   │   └── transaction.py # 交易类
│   ├── network/           # 网络通信
│   │   ├── api.py         # REST API
│   │   └── node.py        # P2P节点
│   └── utils/             # 工具模块
│       ├── crypto.py      # 加密工具
│       └── merkle.py      # Merkle树
├── config/                # 配置文件
├── scripts/               # 启动脚本
├── wallets/               # 钱包存储（自动生成）
└── docs/                  # 文档
```

## 🌟 核心功能

### 1. 数字签名交易系统

```python
# 创建并签名交易
from src.core.transaction import Transaction
from src.utils.crypto import Wallet

wallet = Wallet()
transaction = Transaction("sender", "receiver", 100, fee=1)
transaction.sign_transaction(wallet.private_key)
```

### 2. P2P网络通信

- 自动节点发现
- 区块链同步
- 交易和区块广播
- 故障恢复

### 3. REST API接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/status` | GET | 获取节点状态 |
| `/api/v1/blocks` | GET | 获取所有区块 |
| `/api/v1/transactions` | POST | 创建交易 |
| `/api/v1/balance/{address}` | GET | 查询余额 |
| `/api/v1/mine` | POST | 挖矿 |

### 4. 实时WebSocket

- 新交易通知
- 新区块广播
- 状态更新推送

## 💻 使用示例

### API调用示例

```bash
# 获取节点状态
curl http://localhost:5000/api/v1/status

# 创建交易
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "发送者地址",
    "receiver": "接收者地址", 
    "amount": 100,
    "fee": 1,
    "private_key": "私钥"
  }'

# 挖矿
curl -X POST http://localhost:5000/api/v1/mine \
  -H "Content-Type: application/json" \
  -d '{"miner_address": "矿工地址"}'
```

### Python SDK示例

```python
import requests

# 连接到节点
node_url = "http://localhost:5000/api/v1"

# 获取状态
response = requests.get(f"{node_url}/status")
print(response.json())

# 查询余额
balance = requests.get(f"{node_url}/balance/地址")
print(f"余额: {balance.json()['balance']}")
```

## 🔧 高级配置

### 网络配置

编辑 `config/settings.py`:

```python
# 挖矿难度
MINING_DIFFICULTY = 4

# 网络端口
DEFAULT_PORT = 5000

# 最大对等节点数
MAX_PEERS = 10

# 同步间隔
SYNC_INTERVAL = 10
```

### 启动多节点网络

```bash
# 节点1 (主节点)
python scripts/start_node.py --port 5000 --auto-mine

# 节点2 (连接到节点1)
python scripts/start_node.py --port 5001 --peers localhost:5000

# 节点3 (连接到节点1和2)
python scripts/start_node.py --port 5002 --peers localhost:5000,localhost:5001
```

## 📊 监控和管理

### 区块链状态监控

访问 `http://localhost:5000/api/v1/status` 查看：

- 区块总数
- 交易总数
- 挖矿难度
- 待处理交易数
- 节点连接状态

### 性能指标

- 平均出块时间
- 交易处理能力 (TPS)
- 网络延迟
- 存储使用量

## 🛡️ 安全特性

1. **ECDSA数字签名** - 防止交易伪造
2. **Merkle树验证** - 确保数据完整性  
3. **工作量证明** - 防止双重支付
4. **网络加密** - 保护通信安全
5. **私钥管理** - 安全的钱包系统

## 🧪 测试

```bash
# 运行测试套件
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_blockchain.py
```

## 📈 性能优化

### 建议配置

| 环境 | 难度 | 节点数 | 内存 |
|------|------|--------|------|
| 开发 | 2-3 | 1-3 | 512MB |
| 测试 | 3-4 | 3-5 | 1GB |
| 生产 | 4-6 | 5-10 | 2GB+ |

### 优化建议

1. **降低挖矿难度** - 开发环境使用难度2-3
2. **限制交易池大小** - 防止内存溢出
3. **定期清理日志** - 防止磁盘空间不足
4. **使用SSD存储** - 提高I/O性能

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交修改 (`git commit -am '添加新功能'`)
4. 推送分支 (`git push origin feature/新功能`)
5. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有为区块链技术发展做出贡献的开发者！

---

**⚡ 立即开始体验现代区块链技术！** 