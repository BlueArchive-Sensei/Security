"""
LevelDB存储实现
"""
import os
import json
import plyvel
import threading
from typing import Optional, List, Dict, Any, Iterator
from .storage_interface import StorageInterface, BlockStorageInterface, StateStorageInterface


class LevelDBStorage(StorageInterface, BlockStorageInterface, StateStorageInterface):
    """LevelDB存储实现"""
    
    def __init__(self, db_path: str = "./blockchain_data", 
                 create_if_missing: bool = True,
                 compression: str = 'snappy'):
        """
        初始化LevelDB存储
        
        Args:
            db_path: 数据库路径
            create_if_missing: 如果数据库不存在是否创建
            compression: 压缩算法 ('snappy', 'lz4', None)
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        
        # 创建数据库目录
        os.makedirs(db_path, exist_ok=True)
        
        # 配置压缩
        compression_type = None
        if compression == 'snappy':
            compression_type = 'snappy'
        elif compression == 'lz4':
            compression_type = 'lz4'
        
        try:
            # 打开LevelDB
            self.db = plyvel.DB(
                db_path,
                create_if_missing=create_if_missing,
                compression=compression_type,
                bloom_filter_bits=10,  # 布隆过滤器
                block_cache_size=100 * 1024 * 1024  # 100MB缓存
            )
            print(f"✅ LevelDB存储已初始化: {db_path}")
            
        except Exception as e:
            raise Exception(f"无法初始化LevelDB存储: {e}")
    
    # ========== 基础存储接口实现 ==========
    
    def put(self, key: str, value: bytes) -> bool:
        """存储键值对"""
        try:
            with self.lock:
                self.db.put(key.encode('utf-8'), value)
                return True
        except Exception as e:
            print(f"存储失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[bytes]:
        """获取值"""
        try:
            with self.lock:
                value = self.db.get(key.encode('utf-8'))
                return value
        except Exception as e:
            print(f"读取失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除键值对"""
        try:
            with self.lock:
                self.db.delete(key.encode('utf-8'))
                return True
        except Exception as e:
            print(f"删除失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None
    
    def batch_put(self, items: Dict[str, bytes]) -> bool:
        """批量存储"""
        try:
            with self.lock:
                with self.db.write_batch() as batch:
                    for key, value in items.items():
                        batch.put(key.encode('utf-8'), value)
                return True
        except Exception as e:
            print(f"批量存储失败: {e}")
            return False
    
    def batch_delete(self, keys: List[str]) -> bool:
        """批量删除"""
        try:
            with self.lock:
                with self.db.write_batch() as batch:
                    for key in keys:
                        batch.delete(key.encode('utf-8'))
                return True
        except Exception as e:
            print(f"批量删除失败: {e}")
            return False
    
    def scan(self, prefix: str, limit: int = 100) -> Iterator[tuple]:
        """扫描指定前缀的键值对"""
        try:
            with self.lock:
                prefix_bytes = prefix.encode('utf-8')
                count = 0
                
                for key, value in self.db.iterator(prefix=prefix_bytes):
                    if count >= limit:
                        break
                    yield (key.decode('utf-8'), value)
                    count += 1
                    
        except Exception as e:
            print(f"扫描失败 {prefix}: {e}")
    
    def close(self) -> None:
        """关闭存储连接"""
        try:
            with self.lock:
                if hasattr(self, 'db') and self.db:
                    self.db.close()
                    print("✅ LevelDB连接已关闭")
        except Exception as e:
            print(f"关闭LevelDB失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            # 获取LevelDB统计信息
            stats = {}
            
            # 计算大概的键值对数量
            total_keys = 0
            total_size = 0
            
            for key, value in self.db.iterator():
                total_keys += 1
                total_size += len(key) + len(value)
                if total_keys > 10000:  # 避免扫描过多数据
                    break
            
            stats.update({
                'db_path': self.db_path,
                'estimated_keys': total_keys,
                'estimated_size_bytes': total_size,
                'estimated_size_mb': round(total_size / (1024 * 1024), 2)
            })
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    # ========== 区块存储接口实现 ==========
    
    def store_block(self, block_hash: str, block_data: bytes) -> bool:
        """存储区块"""
        key = f"block:{block_hash}"
        return self.put(key, block_data)
    
    def get_block(self, block_hash: str) -> Optional[bytes]:
        """获取区块"""
        key = f"block:{block_hash}"
        return self.get(key)
    
    def store_block_index(self, block_height: int, block_hash: str) -> bool:
        """存储区块索引"""
        key = f"height:{block_height:010d}"  # 补零对齐，便于排序
        return self.put(key, block_hash.encode('utf-8'))
    
    def get_block_hash_by_height(self, height: int) -> Optional[str]:
        """根据高度获取区块哈希"""
        key = f"height:{height:010d}"
        value = self.get(key)
        return value.decode('utf-8') if value else None
    
    def store_transaction_index(self, tx_hash: str, block_hash: str, tx_index: int) -> bool:
        """存储交易索引"""
        key = f"tx:{tx_hash}"
        location_data = {
            'block_hash': block_hash,
            'tx_index': tx_index
        }
        return self.put(key, json.dumps(location_data).encode('utf-8'))
    
    def get_transaction_location(self, tx_hash: str) -> Optional[tuple]:
        """获取交易位置信息"""
        key = f"tx:{tx_hash}"
        value = self.get(key)
        if value:
            try:
                location_data = json.loads(value.decode('utf-8'))
                return (location_data['block_hash'], location_data['tx_index'])
            except:
                return None
        return None
    
    # ========== 状态存储接口实现 ==========
    
    def store_account_balance(self, address: str, balance: float) -> bool:
        """存储账户余额"""
        key = f"balance:{address}"
        return self.put(key, str(balance).encode('utf-8'))
    
    def get_account_balance(self, address: str) -> Optional[float]:
        """获取账户余额"""
        key = f"balance:{address}"
        value = self.get(key)
        if value:
            try:
                return float(value.decode('utf-8'))
            except:
                return None
        return None
    
    def store_utxo(self, utxo_key: str, utxo_data: bytes) -> bool:
        """存储UTXO"""
        key = f"utxo:{utxo_key}"
        return self.put(key, utxo_data)
    
    def get_utxo(self, utxo_key: str) -> Optional[bytes]:
        """获取UTXO"""
        key = f"utxo:{utxo_key}"
        return self.get(key)
    
    def delete_utxo(self, utxo_key: str) -> bool:
        """删除已花费的UTXO"""
        key = f"utxo:{utxo_key}"
        return self.delete(key)
    
    # ========== 扩展功能 ==========
    
    def get_latest_block_height(self) -> int:
        """获取最新区块高度"""
        try:
            latest_height = -1
            for key, _ in self.scan("height:", limit=1000):
                if key.startswith("height:"):
                    height = int(key.split(":")[1])
                    latest_height = max(latest_height, height)
            return latest_height
        except:
            return -1
    
    def get_all_accounts(self) -> List[str]:
        """获取所有账户地址"""
        accounts = []
        try:
            for key, _ in self.scan("balance:", limit=10000):
                if key.startswith("balance:"):
                    address = key.split(":", 1)[1]
                    accounts.append(address)
        except:
            pass
        return accounts
    
    def backup_to_file(self, backup_path: str) -> bool:
        """备份数据到文件"""
        try:
            backup_data = {}
            
            # 备份所有数据
            for key, value in self.db.iterator():
                key_str = key.decode('utf-8')
                # 根据数据类型进行不同处理
                if key_str.startswith(('balance:', 'height:')):
                    backup_data[key_str] = value.decode('utf-8')
                else:
                    # 对于二进制数据，使用base64编码
                    import base64
                    backup_data[key_str] = base64.b64encode(value).decode('utf-8')
            
            # 写入备份文件
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 数据已备份到: {backup_path}")
            return True
            
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def restore_from_file(self, backup_path: str) -> bool:
        """从文件恢复数据"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 批量恢复数据
            batch_items = {}
            
            for key, value in backup_data.items():
                if key.startswith(('balance:', 'height:')):
                    batch_items[key] = value.encode('utf-8')
                else:
                    # 解码base64数据
                    import base64
                    batch_items[key] = base64.b64decode(value.encode('utf-8'))
            
            # 批量写入
            result = self.batch_put(batch_items)
            
            if result:
                print(f"✅ 数据已从备份恢复: {backup_path}")
            
            return result
            
        except Exception as e:
            print(f"恢复失败: {e}")
            return False 