"""
存储层接口定义
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Iterator


class StorageInterface(ABC):
    """存储层抽象接口"""
    
    @abstractmethod
    def put(self, key: str, value: bytes) -> bool:
        """存储键值对"""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """获取值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除键值对"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def batch_put(self, items: Dict[str, bytes]) -> bool:
        """批量存储"""
        pass
    
    @abstractmethod
    def batch_delete(self, keys: List[str]) -> bool:
        """批量删除"""
        pass
    
    @abstractmethod
    def scan(self, prefix: str, limit: int = 100) -> Iterator[tuple]:
        """扫描指定前缀的键值对"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭存储连接"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass


class BlockStorageInterface(ABC):
    """区块存储接口"""
    
    @abstractmethod
    def store_block(self, block_hash: str, block_data: bytes) -> bool:
        """存储区块"""
        pass
    
    @abstractmethod
    def get_block(self, block_hash: str) -> Optional[bytes]:
        """获取区块"""
        pass
    
    @abstractmethod
    def store_block_index(self, block_height: int, block_hash: str) -> bool:
        """存储区块索引"""
        pass
    
    @abstractmethod
    def get_block_hash_by_height(self, height: int) -> Optional[str]:
        """根据高度获取区块哈希"""
        pass
    
    @abstractmethod
    def store_transaction_index(self, tx_hash: str, block_hash: str, tx_index: int) -> bool:
        """存储交易索引"""
        pass
    
    @abstractmethod
    def get_transaction_location(self, tx_hash: str) -> Optional[tuple]:
        """获取交易位置信息"""
        pass


class StateStorageInterface(ABC):
    """状态存储接口"""
    
    @abstractmethod
    def store_account_balance(self, address: str, balance: float) -> bool:
        """存储账户余额"""
        pass
    
    @abstractmethod
    def get_account_balance(self, address: str) -> Optional[float]:
        """获取账户余额"""
        pass
    
    @abstractmethod
    def store_utxo(self, utxo_key: str, utxo_data: bytes) -> bool:
        """存储UTXO"""
        pass
    
    @abstractmethod
    def get_utxo(self, utxo_key: str) -> Optional[bytes]:
        """获取UTXO"""
        pass
    
    @abstractmethod
    def delete_utxo(self, utxo_key: str) -> bool:
        """删除已花费的UTXO"""
        pass 