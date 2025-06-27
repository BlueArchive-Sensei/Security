"""
存储管理器 - 统一管理区块链数据存储
"""
import json
import time
from typing import Optional, List, Dict, Any
from ..core.block import Block
from ..core.transaction import Transaction

# 尝试导入不同的存储后端
try:
    from .leveldb_storage import LevelDBStorage
    LEVELDB_AVAILABLE = True
except ImportError:
    LEVELDB_AVAILABLE = False
    print("⚠️ LevelDB不可用，将使用SQLite存储")

from .sqlite_storage import SQLiteStorage
from .distributed_storage import DistributedStorage


class StorageManager:
    """存储管理器 - 为区块链提供统一的存储接口"""
    
    def __init__(self, storage_config: Dict[str, Any]):
        """
        初始化存储管理器
        
        Args:
            storage_config: 存储配置
            {
                'type': 'leveldb' | 'sqlite' | 'distributed',
                'path': './blockchain_data',
                'compression': 'snappy',
                'distributed': {
                    'peers': ['http://node1:5000'],
                    'replication_factor': 2,
                    'consistency_level': 'quorum'
                }
            }
        """
        self.config = storage_config
        self.storage_type = storage_config.get('type', 'sqlite')
        
        # 如果指定了LevelDB但不可用，则降级到SQLite
        if self.storage_type == 'leveldb' and not LEVELDB_AVAILABLE:
            print("⚠️ LevelDB不可用，自动切换到SQLite存储")
            self.storage_type = 'sqlite'
            storage_config['type'] = 'sqlite'
        
        # 初始化本地存储
        if self.storage_type == 'leveldb' and LEVELDB_AVAILABLE:
            self.local_storage = LevelDBStorage(
                db_path=storage_config.get('path', './blockchain_data'),
                compression=storage_config.get('compression', 'snappy')
            )
        else:
            # 使用SQLite存储
            db_path = storage_config.get('path', './blockchain_data')
            if not db_path.endswith('.db'):
                db_path += '.db'
            self.local_storage = SQLiteStorage(db_path=db_path)
        
        # 如果配置了分布式存储
        if self.storage_type == 'distributed':
            dist_config = storage_config.get('distributed', {})
            self.storage = DistributedStorage(
                local_storage=self.local_storage,
                peer_nodes=dist_config.get('peers', []),
                replication_factor=dist_config.get('replication_factor', 2),
                consistency_level=dist_config.get('consistency_level', 'quorum')
            )
        else:
            self.storage = self.local_storage
        
        print(f"✅ 存储管理器已初始化 (类型: {self.storage_type})")
    
    # ========== 区块存储管理 ==========
    
    def store_block(self, block: Block) -> bool:
        """存储区块及其索引"""
        try:
            # 序列化区块数据
            block_data = json.dumps(block.to_dict()).encode('utf-8')
            
            # 存储区块内容
            if not self.local_storage.store_block(block.hash, block_data):
                return False
            
            # 存储区块高度索引
            if not self.local_storage.store_block_index(block.index, block.hash):
                return False
            
            # 存储交易索引
            for tx_index, transaction in enumerate(block.transactions):
                if not self.local_storage.store_transaction_index(
                    transaction.transaction_id, block.hash, tx_index):
                    print(f"警告: 交易索引存储失败 {transaction.transaction_id}")
            
            return True
            
        except Exception as e:
            print(f"存储区块失败: {e}")
            return False
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """根据哈希获取区块"""
        try:
            block_data = self.local_storage.get_block(block_hash)
            if block_data:
                block_dict = json.loads(block_data.decode('utf-8'))
                return Block.from_dict(block_dict)
            return None
        except Exception as e:
            print(f"获取区块失败 {block_hash}: {e}")
            return None
    
    def get_block_by_height(self, height: int) -> Optional[Block]:
        """根据高度获取区块"""
        try:
            block_hash = self.local_storage.get_block_hash_by_height(height)
            if block_hash:
                return self.get_block_by_hash(block_hash)
            return None
        except Exception as e:
            print(f"获取区块失败 (高度 {height}): {e}")
            return None
    
    def get_latest_block_height(self) -> int:
        """获取最新区块高度"""
        return self.local_storage.get_latest_block_height()
    
    # ========== 交易存储管理 ==========
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[tuple]:
        """根据哈希获取交易"""
        try:
            location = self.local_storage.get_transaction_location(tx_hash)
            if location:
                block_hash, tx_index = location
                block = self.get_block_by_hash(block_hash)
                if block and tx_index < len(block.transactions):
                    return block.transactions[tx_index], block.index
            return None
        except Exception as e:
            print(f"获取交易失败 {tx_hash}: {e}")
            return None
    
    # ========== 状态存储管理 ==========
    
    def store_balances(self, balances: Dict[str, float]) -> bool:
        """批量存储账户余额"""
        try:
            success_count = 0
            for address, balance in balances.items():
                if self.local_storage.store_account_balance(address, balance):
                    success_count += 1
            
            return success_count == len(balances)
            
        except Exception as e:
            print(f"存储余额失败: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """获取账户余额"""
        balance = self.local_storage.get_account_balance(address)
        return balance if balance is not None else 0.0
    
    def get_all_balances(self) -> Dict[str, float]:
        """获取所有账户余额"""
        balances = {}
        try:
            accounts = self.local_storage.get_all_accounts()
            for address in accounts:
                balance = self.get_balance(address)
                if balance > 0:
                    balances[address] = balance
        except Exception as e:
            print(f"获取所有余额失败: {e}")
        
        return balances
    
    # ========== 链状态管理 ==========
    
    def store_blockchain_metadata(self, metadata: Dict[str, Any]) -> bool:
        """存储区块链元数据"""
        try:
            metadata_json = json.dumps(metadata).encode('utf-8')
            return self.storage.put("blockchain:metadata", metadata_json)
        except Exception as e:
            print(f"存储元数据失败: {e}")
            return False
    
    def get_blockchain_metadata(self) -> Dict[str, Any]:
        """获取区块链元数据"""
        try:
            data = self.storage.get("blockchain:metadata")
            if data:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"获取元数据失败: {e}")
        
        return {
            'difficulty': 4,
            'mining_reward': 50.0,
            'created_at': time.time()
        }
    
    def store_last_sync_time(self, timestamp: float) -> bool:
        """存储最后同步时间"""
        return self.storage.put("sync:last_time", str(timestamp).encode('utf-8'))
    
    def get_last_sync_time(self) -> float:
        """获取最后同步时间"""
        try:
            data = self.storage.get("sync:last_time")
            if data:
                return float(data.decode('utf-8'))
        except:
            pass
        return 0.0
    
    # ========== 数据同步与备份 ==========
    
    def export_blockchain_data(self, export_path: str) -> bool:
        """导出区块链数据"""
        try:
            export_data = {
                'metadata': self.get_blockchain_metadata(),
                'blocks': [],
                'balances': self.get_all_balances(),
                'export_time': time.time()
            }
            
            # 导出所有区块
            latest_height = self.get_latest_block_height()
            for height in range(latest_height + 1):
                block = self.get_block_by_height(height)
                if block:
                    export_data['blocks'].append(block.to_dict())
            
            # 写入文件
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 区块链数据已导出到: {export_path}")
            return True
            
        except Exception as e:
            print(f"导出数据失败: {e}")
            return False
    
    def import_blockchain_data(self, import_path: str) -> bool:
        """导入区块链数据"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入元数据
            if 'metadata' in import_data:
                self.store_blockchain_metadata(import_data['metadata'])
            
            # 导入区块
            if 'blocks' in import_data:
                for block_dict in import_data['blocks']:
                    block = Block.from_dict(block_dict)
                    self.store_block(block)
            
            # 导入余额
            if 'balances' in import_data:
                self.store_balances(import_data['balances'])
            
            print(f"✅ 区块链数据已从文件导入: {import_path}")
            return True
            
        except Exception as e:
            print(f"导入数据失败: {e}")
            return False
    
    def backup_storage(self, backup_path: str) -> bool:
        """备份存储数据"""
        return self.local_storage.backup_to_file(backup_path)
    
    def restore_storage(self, backup_path: str) -> bool:
        """恢复存储数据"""
        return self.local_storage.restore_from_file(backup_path)
    
    # ========== 存储统计和管理 ==========
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = self.storage.get_stats()
        
        # 添加区块链特定统计
        blockchain_stats = {
            'latest_block_height': self.get_latest_block_height(),
            'total_accounts': len(self.get_all_balances()),
            'storage_type': self.storage_type
        }
        
        stats.update(blockchain_stats)
        return stats
    
    def cleanup_old_data(self, keep_blocks: int = 1000) -> bool:
        """清理旧数据（保留最近的区块）"""
        try:
            latest_height = self.get_latest_block_height()
            if latest_height <= keep_blocks:
                return True  # 不需要清理
            
            # 对于SQLite，可以删除旧的区块记录
            # 对于LevelDB，删除旧区块的索引
            cleanup_height = latest_height - keep_blocks
            
            if hasattr(self.local_storage, 'conn'):  # SQLite
                # SQLite特定的清理逻辑
                with self.local_storage.lock:
                    cursor = self.local_storage.conn.cursor()
                    cursor.execute('DELETE FROM block_height_index WHERE height < ?', (cleanup_height,))
                    cursor.execute('DELETE FROM blocks WHERE block_height < ?', (cleanup_height,))
                    self.local_storage.conn.commit()
                    
                    print(f"✅ 已清理高度小于 {cleanup_height} 的旧区块")
                    return True
            else:  # LevelDB
                delete_keys = []
                for height in range(cleanup_height):
                    height_key = f"height:{height:010d}"
                    delete_keys.append(height_key)
                
                result = self.storage.batch_delete(delete_keys)
                if result:
                    print(f"✅ 已清理 {len(delete_keys)} 个旧区块索引")
                return result
            
        except Exception as e:
            print(f"清理数据失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭存储管理器"""
        self.storage.close()
        print("✅ 存储管理器已关闭") 