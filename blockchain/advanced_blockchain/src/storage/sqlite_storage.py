"""
SQLite存储实现 - LevelDB的替代方案
"""
import os
import json
import sqlite3
import threading
import time
from typing import Optional, List, Dict, Any, Iterator
from .storage_interface import StorageInterface, BlockStorageInterface, StateStorageInterface


class SQLiteStorage(StorageInterface, BlockStorageInterface, StateStorageInterface):
    """SQLite存储实现"""
    
    def __init__(self, db_path: str = "./blockchain_data.db", 
                 create_if_missing: bool = True):
        """
        初始化SQLite存储
        
        Args:
            db_path: 数据库文件路径
            create_if_missing: 如果数据库不存在是否创建
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        
        # 创建数据库目录
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        try:
            # 初始化数据库连接
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式提高并发性能
            self.conn.execute("PRAGMA synchronous=NORMAL")  # 平衡安全性和性能
            self.conn.execute("PRAGMA cache_size=10000")  # 增大缓存
            
            # 创建表结构
            self._create_tables()
            
            print(f"✅ SQLite存储已初始化: {db_path}")
            
        except Exception as e:
            raise Exception(f"无法初始化SQLite存储: {e}")
    
    def _create_tables(self):
        """创建数据库表"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # 通用键值对表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_value (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL DEFAULT (julianday('now')),
                    updated_at REAL DEFAULT (julianday('now'))
                )
            ''')
            
            # 区块表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    block_hash TEXT PRIMARY KEY,
                    block_data BLOB,
                    block_height INTEGER,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            
            # 区块高度索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS block_height_index (
                    height INTEGER PRIMARY KEY,
                    block_hash TEXT,
                    FOREIGN KEY (block_hash) REFERENCES blocks (block_hash)
                )
            ''')
            
            # 交易索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_index (
                    tx_hash TEXT PRIMARY KEY,
                    block_hash TEXT,
                    tx_index INTEGER,
                    FOREIGN KEY (block_hash) REFERENCES blocks (block_hash)
                )
            ''')
            
            # 账户余额表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_balances (
                    address TEXT PRIMARY KEY,
                    balance REAL,
                    updated_at REAL DEFAULT (julianday('now'))
                )
            ''')
            
            # UTXO表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utxos (
                    utxo_key TEXT PRIMARY KEY,
                    utxo_data BLOB,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(block_height)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_key_value_key ON key_value(key)')
            
            self.conn.commit()
    
    # ========== 基础存储接口实现 ==========
    
    def put(self, key: str, value: bytes) -> bool:
        """存储键值对"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO key_value (key, value, updated_at) VALUES (?, ?, julianday("now"))',
                    (key, value)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[bytes]:
        """获取值"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT value FROM key_value WHERE key = ?', (key,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"读取失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除键值对"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM key_value WHERE key = ?', (key,))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"删除失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT 1 FROM key_value WHERE key = ? LIMIT 1', (key,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"检查存在性失败 {key}: {e}")
            return False
    
    def batch_put(self, items: Dict[str, bytes]) -> bool:
        """批量存储"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                data = [(key, value, time.time()) for key, value in items.items()]
                cursor.executemany(
                    'INSERT OR REPLACE INTO key_value (key, value, updated_at) VALUES (?, ?, julianday("now"))',
                    [(key, value) for key, value in items.items()]
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"批量存储失败: {e}")
            return False
    
    def batch_delete(self, keys: List[str]) -> bool:
        """批量删除"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.executemany('DELETE FROM key_value WHERE key = ?', [(key,) for key in keys])
                self.conn.commit()
                return True
        except Exception as e:
            print(f"批量删除失败: {e}")
            return False
    
    def scan(self, prefix: str, limit: int = 100) -> Iterator[tuple]:
        """扫描指定前缀的键值对"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT key, value FROM key_value WHERE key LIKE ? LIMIT ?',
                    (f'{prefix}%', limit)
                )
                
                for row in cursor.fetchall():
                    yield (row[0], row[1])
                    
        except Exception as e:
            print(f"扫描失败 {prefix}: {e}")
    
    def close(self) -> None:
        """关闭存储连接"""
        try:
            with self.lock:
                if hasattr(self, 'conn') and self.conn:
                    self.conn.close()
                    print("✅ SQLite连接已关闭")
        except Exception as e:
            print(f"关闭SQLite失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                
                # 获取各表的统计信息
                stats = {'db_path': self.db_path}
                
                # 键值对统计
                cursor.execute('SELECT COUNT(*) FROM key_value')
                stats['total_keys'] = cursor.fetchone()[0]
                
                # 区块统计
                cursor.execute('SELECT COUNT(*) FROM blocks')
                stats['total_blocks'] = cursor.fetchone()[0]
                
                # 账户统计
                cursor.execute('SELECT COUNT(*) FROM account_balances')
                stats['total_accounts'] = cursor.fetchone()[0]
                
                # 数据库大小
                stats['db_size_bytes'] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
                
                return stats
                
        except Exception as e:
            return {'error': str(e)}
    
    # ========== 区块存储接口实现 ==========
    
    def store_block(self, block_hash: str, block_data: bytes) -> bool:
        """存储区块"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                
                # 从区块数据中提取高度（假设是JSON格式）
                try:
                    block_dict = json.loads(block_data.decode('utf-8'))
                    block_height = block_dict.get('index', 0)
                except:
                    block_height = 0
                
                cursor.execute(
                    'INSERT OR REPLACE INTO blocks (block_hash, block_data, block_height) VALUES (?, ?, ?)',
                    (block_hash, block_data, block_height)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储区块失败 {block_hash}: {e}")
            return False
    
    def get_block(self, block_hash: str) -> Optional[bytes]:
        """获取区块"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT block_data FROM blocks WHERE block_hash = ?', (block_hash,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"获取区块失败 {block_hash}: {e}")
            return None
    
    def store_block_index(self, block_height: int, block_hash: str) -> bool:
        """存储区块索引"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO block_height_index (height, block_hash) VALUES (?, ?)',
                    (block_height, block_hash)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储区块索引失败 {block_height}: {e}")
            return False
    
    def get_block_hash_by_height(self, height: int) -> Optional[str]:
        """根据高度获取区块哈希"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT block_hash FROM block_height_index WHERE height = ?', (height,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"获取区块哈希失败 {height}: {e}")
            return None
    
    def store_transaction_index(self, tx_hash: str, block_hash: str, tx_index: int) -> bool:
        """存储交易索引"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO transaction_index (tx_hash, block_hash, tx_index) VALUES (?, ?, ?)',
                    (tx_hash, block_hash, tx_index)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储交易索引失败 {tx_hash}: {e}")
            return False
    
    def get_transaction_location(self, tx_hash: str) -> Optional[tuple]:
        """获取交易位置信息"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT block_hash, tx_index FROM transaction_index WHERE tx_hash = ?', (tx_hash,))
                result = cursor.fetchone()
                return (result[0], result[1]) if result else None
        except Exception as e:
            print(f"获取交易位置失败 {tx_hash}: {e}")
            return None
    
    # ========== 状态存储接口实现 ==========
    
    def store_account_balance(self, address: str, balance: float) -> bool:
        """存储账户余额"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO account_balances (address, balance, updated_at) VALUES (?, ?, julianday("now"))',
                    (address, balance)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储账户余额失败 {address}: {e}")
            return False
    
    def get_account_balance(self, address: str) -> Optional[float]:
        """获取账户余额"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT balance FROM account_balances WHERE address = ?', (address,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"获取账户余额失败 {address}: {e}")
            return None
    
    def store_utxo(self, utxo_key: str, utxo_data: bytes) -> bool:
        """存储UTXO"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO utxos (utxo_key, utxo_data) VALUES (?, ?)',
                    (utxo_key, utxo_data)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"存储UTXO失败 {utxo_key}: {e}")
            return False
    
    def get_utxo(self, utxo_key: str) -> Optional[bytes]:
        """获取UTXO"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT utxo_data FROM utxos WHERE utxo_key = ?', (utxo_key,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"获取UTXO失败 {utxo_key}: {e}")
            return None
    
    def delete_utxo(self, utxo_key: str) -> bool:
        """删除已花费的UTXO"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM utxos WHERE utxo_key = ?', (utxo_key,))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"删除UTXO失败 {utxo_key}: {e}")
            return False
    
    # ========== 扩展功能 ==========
    
    def get_latest_block_height(self) -> int:
        """获取最新区块高度"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT MAX(height) FROM block_height_index')
                result = cursor.fetchone()
                return result[0] if result[0] is not None else -1
        except Exception as e:
            print(f"获取最新区块高度失败: {e}")
            return -1
    
    def get_all_accounts(self) -> List[str]:
        """获取所有账户地址"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT address FROM account_balances')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取所有账户失败: {e}")
            return []
    
    def backup_to_file(self, backup_path: str) -> bool:
        """备份数据到文件"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                
                backup_data = {
                    'key_value': [],
                    'blocks': [],
                    'block_height_index': [],
                    'transaction_index': [],
                    'account_balances': [],
                    'utxos': []
                }
                
                # 备份各表数据
                for table_name in backup_data.keys():
                    cursor.execute(f'SELECT * FROM {table_name}')
                    rows = cursor.fetchall()
                    
                    # 获取列名
                    column_names = [description[0] for description in cursor.description]
                    
                    # 转换为字典格式
                    for row in rows:
                        row_dict = dict(zip(column_names, row))
                        
                        # 处理二进制数据
                        for key, value in row_dict.items():
                            if isinstance(value, bytes):
                                import base64
                                row_dict[key] = base64.b64encode(value).decode('utf-8')
                        
                        backup_data[table_name].append(row_dict)
                
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
            
            with self.lock:
                cursor = self.conn.cursor()
                
                # 清空现有数据
                for table_name in backup_data.keys():
                    cursor.execute(f'DELETE FROM {table_name}')
                
                # 恢复数据
                for table_name, rows in backup_data.items():
                    if not rows:
                        continue
                    
                    # 获取列名
                    columns = list(rows[0].keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    
                    for row_dict in rows:
                        # 处理base64编码的二进制数据
                        values = []
                        for col in columns:
                            value = row_dict[col]
                            if col in ['value', 'block_data', 'utxo_data'] and isinstance(value, str):
                                import base64
                                try:
                                    value = base64.b64decode(value.encode('utf-8'))
                                except:
                                    pass
                            values.append(value)
                        
                        cursor.execute(
                            f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})',
                            values
                        )
                
                self.conn.commit()
                print(f"✅ 数据已从备份恢复: {backup_path}")
                return True
                
        except Exception as e:
            print(f"恢复失败: {e}")
            return False 