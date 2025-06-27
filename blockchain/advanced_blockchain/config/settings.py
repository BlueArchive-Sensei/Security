"""
区块链节点配置文件
"""
import os

# 网络配置
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
DEFAULT_WS_PORT = 5001

# 区块链配置
MINING_DIFFICULTY = 4
BLOCK_TIME = 10  # 期望的出块时间（秒）
MAX_TRANSACTIONS_PER_BLOCK = 100
MINING_REWARD = 50

# P2P网络配置
MAX_PEERS = 10
PEER_DISCOVERY_INTERVAL = 30
SYNC_INTERVAL = 10

# 存储配置
DATABASE_PATH = "blockchain_data"
WALLET_PATH = "wallets"

# API配置
API_PREFIX = "/api/v1"
ENABLE_CORS = True

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 开发环境配置
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "blockchain-secret-key-change-in-production")

# 节点类型
NODE_TYPE = os.getenv("NODE_TYPE", "full")  # full, light, mining 