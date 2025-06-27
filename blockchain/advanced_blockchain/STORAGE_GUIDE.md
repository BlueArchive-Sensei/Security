# 区块链存储层使用指南

本指南介绍如何使用区块链系统的存储层，包括集中式LevelDB存储和分布式存储的配置与部署。

## 📖 目录

- [存储层概述](#存储层概述)
- [LevelDB存储](#leveldb存储)
- [分布式存储](#分布式存储)
- [存储配置](#存储配置)
- [API接口](#api接口)
- [部署指南](#部署指南)
- [性能优化](#性能优化)
- [故障排除](#故障排除)

## 存储层概述

我们的区块链系统提供了灵活的存储层架构，支持：

### 🏗️ 架构特性
- **模块化设计**: 支持不同存储后端
- **统一接口**: 标准化的存储API
- **高性能**: 基于LevelDB的优化存储
- **分布式支持**: 多节点数据复制和一致性
- **数据压缩**: 支持Snappy和LZ4压缩
- **自动备份**: 内置数据导出/导入功能

### 🔧 存储类型
1. **LevelDB存储**: 单机高性能键值存储
2. **分布式存储**: 多节点数据复制和同步

## LevelDB存储

### 基本配置

```python
storage_config = {
    'type': 'leveldb',
    'path': './blockchain_data',
    'compression': 'snappy'  # 'snappy', 'lz4', None
}

blockchain = Blockchain(storage_config=storage_config)
```

### 特性说明

- **高性能**: 优化的写入和查询性能
- **数据压缩**: 减少存储空间占用
- **事务支持**: 原子性批量操作
- **布隆过滤器**: 快速存在性检查
- **缓存机制**: 100MB内存缓存

### 性能参数

```python
# 在LevelDB初始化时的优化参数
db = plyvel.DB(
    db_path,
    create_if_missing=True,
    compression='snappy',
    bloom_filter_bits=10,      # 布隆过滤器位数
    block_cache_size=100 * 1024 * 1024  # 100MB缓存
)
```

## 分布式存储

### 基本配置

```python
storage_config = {
    'type': 'distributed',
    'path': './blockchain_data',
    'compression': 'snappy',
    'distributed': {
        'peers': [
            'http://node1.example.com:5000',
            'http://node2.example.com:5000'
        ],
        'replication_factor': 3,        # 数据复制份数
        'consistency_level': 'quorum'   # 一致性级别
    }
}
```

### 一致性级别

1. **strong**: 强一致性 - 所有节点必须写入成功
2. **quorum**: 法定人数 - 大多数节点写入成功即可
3. **eventual**: 最终一致性 - 异步复制，最快响应

### 复制策略

- **一致性哈希**: 基于键哈希值选择存储节点
- **自动容错**: 节点故障时自动路由到健康节点
- **数据同步**: 支持节点间数据同步和修复

## 存储配置

### 完整配置示例

```python
# 生产环境配置
production_config = {
    'type': 'distributed',
    'path': '/var/lib/blockchain/data',
    'compression': 'lz4',
    'distributed': {
        'peers': [
            'http://blockchain-node-1:5000',
            'http://blockchain-node-2:5000',
            'http://blockchain-node-3:5000'
        ],
        'replication_factor': 3,
        'consistency_level': 'quorum'
    }
}

# 开发环境配置
development_config = {
    'type': 'leveldb',
    'path': './dev_blockchain_data',
    'compression': 'snappy'
}
```

### 环境变量配置

```bash
# 设置存储配置环境变量
export BLOCKCHAIN_STORAGE_TYPE=distributed
export BLOCKCHAIN_STORAGE_PATH=/data/blockchain
export BLOCKCHAIN_STORAGE_COMPRESSION=lz4
export BLOCKCHAIN_PEERS=node1:5000,node2:5000,node3:5000
export BLOCKCHAIN_REPLICATION_FACTOR=3
export BLOCKCHAIN_CONSISTENCY_LEVEL=quorum
```

## API接口

### 存储健康检查

```bash
curl http://localhost:5000/api/v1/storage/health
```

### 获取存储统计

```bash
curl http://localhost:5000/api/v1/storage/stats
```

### 数据备份

```bash
curl -X POST http://localhost:5000/api/v1/storage/backup \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "./backup_2024.json"}'
```

### 数据恢复

```bash
curl -X POST http://localhost:5000/api/v1/storage/restore \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "./backup_2024.json"}'
```

### 区块链数据导出

```bash
curl -X POST http://localhost:5000/api/v1/storage/export \
  -H "Content-Type: application/json" \
  -d '{"export_path": "./blockchain_export.json"}'
```

### 清理旧数据

```bash
curl -X POST http://localhost:5000/api/v1/storage/cleanup \
  -H "Content-Type: application/json" \
  -d '{"keep_blocks": 1000}'
```

### 分布式集群管理

```bash
# 获取集群状态
curl http://localhost:5000/api/v1/storage/cluster/status

# 添加对等节点
curl -X POST http://localhost:5000/api/v1/storage/cluster/add-peer \
  -H "Content-Type: application/json" \
  -d '{"peer_url": "http://new-node:5000"}'

# 移除对等节点
curl -X POST http://localhost:5000/api/v1/storage/cluster/remove-peer \
  -H "Content-Type: application/json" \
  -d '{"peer_url": "http://old-node:5000"}'
```

## 部署指南

### 单节点部署

```bash
# 启动单节点（LevelDB存储）
python scripts/start_node.py \
  --port 5000 \
  --storage-type leveldb \
  --storage-path /data/blockchain \
  --compression snappy \
  --auto-mine
```

### 分布式集群部署

#### 节点1部署
```bash
python scripts/start_node.py \
  --port 5000 \
  --storage-type distributed \
  --storage-path /data/blockchain/node1 \
  --compression lz4 \
  --replication-factor 3 \
  --consistency-level quorum \
  --auto-mine
```

#### 节点2部署
```bash
python scripts/start_node.py \
  --port 5001 \
  --storage-type distributed \
  --storage-path /data/blockchain/node2 \
  --peers localhost:5000 \
  --compression lz4 \
  --replication-factor 3 \
  --consistency-level quorum
```

#### 节点3部署
```bash
python scripts/start_node.py \
  --port 5002 \
  --storage-type distributed \
  --storage-path /data/blockchain/node3 \
  --peers localhost:5000,localhost:5001 \
  --compression lz4 \
  --replication-factor 3 \
  --consistency-level quorum
```

### Docker部署

#### 单节点Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

VOLUME ["/data"]

EXPOSE 5000

CMD ["python", "scripts/start_node.py", \
     "--port", "5000", \
     "--storage-type", "leveldb", \
     "--storage-path", "/data/blockchain", \
     "--compression", "snappy", \
     "--auto-mine"]
```

#### 分布式Docker Compose
```yaml
version: '3.8'

services:
  blockchain-node-1:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data/node1:/data
    command: >
      python scripts/start_node.py
      --port 5000
      --storage-type distributed
      --storage-path /data/blockchain
      --compression lz4
      --replication-factor 3
      --consistency-level quorum
      --auto-mine

  blockchain-node-2:
    build: .
    ports:
      - "5001:5000"
    volumes:
      - ./data/node2:/data
    depends_on:
      - blockchain-node-1
    command: >
      python scripts/start_node.py
      --port 5000
      --storage-type distributed
      --storage-path /data/blockchain
      --peers blockchain-node-1:5000
      --compression lz4
      --replication-factor 3
      --consistency-level quorum

  blockchain-node-3:
    build: .
    ports:
      - "5002:5000"
    volumes:
      - ./data/node3:/data
    depends_on:
      - blockchain-node-1
      - blockchain-node-2
    command: >
      python scripts/start_node.py
      --port 5000
      --storage-type distributed
      --storage-path /data/blockchain
      --peers blockchain-node-1:5000,blockchain-node-2:5000
      --compression lz4
      --replication-factor 3
      --consistency-level quorum
```

## 性能优化

### LevelDB优化

#### 系统级优化
```bash
# 增加文件描述符限制
ulimit -n 65536

# 优化内核参数
echo 'vm.swappiness=1' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
```

#### 应用级优化
```python
# 批量写入优化
storage_manager = StorageManager(storage_config)

# 使用批量操作提高性能
batch_items = {}
for i in range(1000):
    key = f"key_{i}"
    value = f"value_{i}".encode('utf-8')
    batch_items[key] = value

storage_manager.storage.batch_put(batch_items)
```

### 分布式存储优化

#### 网络优化
```python
# 连接池配置
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

#### 一致性配置
```python
# 读多写少场景：使用最终一致性
'consistency_level': 'eventual'

# 强一致性要求场景：使用强一致性
'consistency_level': 'strong'

# 平衡性能和一致性：使用法定人数
'consistency_level': 'quorum'
```

## 故障排除

### 常见问题

#### 1. LevelDB启动失败
```bash
# 错误：无法创建数据库
# 解决：检查目录权限
sudo chown -R $(whoami):$(whoami) /data/blockchain
chmod 755 /data/blockchain
```

#### 2. 分布式节点连接失败
```bash
# 错误：无法连接到对等节点
# 解决：检查网络连通性
curl http://peer-node:5000/api/v1/storage/health

# 检查防火墙设置
sudo ufw allow 5000
```

#### 3. 数据不一致
```bash
# 解决：触发数据同步
curl -X POST http://localhost:5000/api/v1/storage/cluster/sync
```

#### 4. 存储空间不足
```bash
# 清理旧数据
curl -X POST http://localhost:5000/api/v1/storage/cleanup \
  -d '{"keep_blocks": 1000}'

# 压缩数据库
# LevelDB会自动进行压缩，也可以手动触发
```

### 监控指标

#### 关键指标监控
- 存储大小和增长率
- 读写操作延迟
- 节点健康状态
- 数据复制状态
- 网络连接状态

#### 监控脚本示例
```bash
#!/bin/bash
# storage_monitor.sh

while true; do
    echo "$(date): 检查存储状态"
    
    # 获取存储统计
    curl -s http://localhost:5000/api/v1/storage/stats | jq '.'
    
    # 检查集群状态
    curl -s http://localhost:5000/api/v1/storage/cluster/status | jq '.'
    
    sleep 60
done
```

### 日志分析

#### 存储相关日志
```bash
# 查看存储错误
grep "存储失败\|LevelDB\|分布式存储" blockchain.log

# 查看性能相关日志
grep "存储统计\|延迟\|大小" blockchain.log

# 查看网络相关日志
grep "复制\|节点\|健康检查" blockchain.log
```

## 最佳实践

### 生产环境建议

1. **存储路径**: 使用独立的高性能磁盘
2. **备份策略**: 定期自动备份和异地存储
3. **监控告警**: 设置存储空间和性能监控
4. **容量规划**: 根据业务增长预估存储需求
5. **安全加固**: 设置适当的文件权限和网络安全

### 开发环境建议

1. **快速启动**: 使用LevelDB单节点模式
2. **数据重置**: 提供快速清理和重建功能
3. **调试支持**: 启用详细日志记录
4. **测试数据**: 使用小数据集进行功能测试

---

📝 **更多信息**: 查看 [TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md) 了解存储层的技术实现细节。 