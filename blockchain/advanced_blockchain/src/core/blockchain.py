"""
区块链核心类
"""
import json
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from .block import Block, GenesisBlock
from .transaction import Transaction, TransactionPool
from ..utils.crypto import CryptoUtils
from ..storage.storage_manager import StorageManager


class Blockchain:
    """区块链类"""
    
    def __init__(self, difficulty: int = 4, mining_reward: float = 50.0,
                 storage_config: Dict[str, Any] = None):
        """
        初始化区块链
        
        Args:
            difficulty: 挖矿难度
            mining_reward: 挖矿奖励
            storage_config: 存储配置
        """
        self.difficulty = difficulty
        self.mining_reward = mining_reward
        self.pending_transactions = []
        self.balances = {}
        self.lock = threading.RLock()
        
        # 初始化存储管理器
        if storage_config is None:
            storage_config = {
                'type': 'leveldb',
                'path': './blockchain_data',
                'compression': 'snappy'
            }
        
        self.storage_manager = StorageManager(storage_config)
        
        # 从存储加载区块链状态
        self._load_from_storage()
        
        print(f"✅ 区块链已初始化 (难度: {difficulty}, 奖励: {mining_reward})")
        
    def _load_from_storage(self):
        """从存储加载区块链状态"""
        try:
            # 加载元数据
            metadata = self.storage_manager.get_blockchain_metadata()
            self.difficulty = metadata.get('difficulty', self.difficulty)
            self.mining_reward = metadata.get('mining_reward', self.mining_reward)
            
            # 加载余额状态
            self.balances = self.storage_manager.get_all_balances()
            
            # 检查创世区块
            if self.storage_manager.get_latest_block_height() == -1:
                self._create_genesis_block()
            
            print(f"✅ 从存储加载区块链状态完成")
            
        except Exception as e:
            print(f"加载区块链状态失败: {e}")
            self._create_genesis_block()
    
    def _save_to_storage(self):
        """保存区块链状态到存储"""
        try:
            # 保存元数据
            metadata = {
                'difficulty': self.difficulty,
                'mining_reward': self.mining_reward,
                'last_updated': time.time()
            }
            self.storage_manager.store_blockchain_metadata(metadata)
            
            # 保存余额状态
            self.storage_manager.store_balances(self.balances)
            
        except Exception as e:
            print(f"保存区块链状态失败: {e}")
    
    def _create_genesis_block(self) -> None:
        """创建创世区块"""
        genesis_transactions = []
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            previous_hash="0"
        )
        # 手动设置nonce
        genesis_block.nonce = 0
        genesis_block.hash = genesis_block._calculate_hash()
        
        # 存储创世区块
        self.storage_manager.store_block(genesis_block)
        print("✅ 创世区块已创建")
    
    @property
    def chain(self) -> List[Block]:
        """获取区块链（用于兼容性）"""
        blocks = []
        latest_height = self.storage_manager.get_latest_block_height()
        
        for height in range(latest_height + 1):
            block = self.storage_manager.get_block_by_height(height)
            if block:
                blocks.append(block)
        
        return blocks
    
    def get_latest_block(self) -> Optional[Block]:
        """获取最新区块"""
        latest_height = self.storage_manager.get_latest_block_height()
        if latest_height >= 0:
            return self.storage_manager.get_block_by_height(latest_height)
        return None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """根据哈希获取区块"""
        return self.storage_manager.get_block_by_hash(block_hash)
    
    def get_block_by_height(self, height: int) -> Optional[Block]:
        """根据高度获取区块"""
        return self.storage_manager.get_block_by_height(height)
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """添加交易到待处理队列"""
        with self.lock:
            if self.validate_transaction(transaction):
                self.pending_transactions.append(transaction)
                return True
            return False
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """验证交易"""
        # 验证交易
        if not transaction.is_valid():
            print(f"交易验证失败: {transaction.transaction_id}")
            return False
        
        # 检查发送者余额
        sender_balance = self.get_balance(transaction.sender)
        total_cost = transaction.amount + transaction.fee
        
        if sender_balance < total_cost:
            print(f"余额不足: {transaction.sender} 余额 {sender_balance}, 需要 {total_cost}")
            return False
        
        return True
    
    def mine_pending_transactions(self, mining_reward_address: str) -> Optional[Block]:
        """挖矿处理待处理交易"""
        with self.lock:
            if not self.pending_transactions:
                return None
            
            # 添加挖矿奖励交易
            reward_transaction = Transaction(
                sender="",
                receiver=mining_reward_address,
                amount=self.mining_reward
            )
            
            # 创建新区块
            latest_block = self.get_latest_block()
            previous_hash = latest_block.hash if latest_block else "0"
            new_index = latest_block.index + 1 if latest_block else 0
            
            transactions = self.pending_transactions.copy()
            transactions.append(reward_transaction)
            
            new_block = Block(
                index=new_index,
                transactions=transactions,
                previous_hash=previous_hash
            )
            
            # 执行工作量证明
            self._mine_block(new_block)
            
            # 存储区块
            if self.storage_manager.store_block(new_block):
                # 更新余额
                self._update_balances_from_block(new_block)
                
                # 清空待处理交易
                self.pending_transactions.clear()
                
                # 保存状态
                self._save_to_storage()
                
                print(f"✅ 区块 {new_index} 挖矿成功: {new_block.hash}")
                return new_block
            
            return None
    
    def _mine_block(self, block: Block):
        """挖矿算法"""
        target = "0" * self.difficulty
        
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block._calculate_hash()
    
    def _update_balances_from_block(self, block: Block):
        """从区块更新余额状态"""
        for transaction in block.transactions:
            # 扣除发送方余额
            if transaction.sender:
                if transaction.sender not in self.balances:
                    self.balances[transaction.sender] = 0
                self.balances[transaction.sender] -= transaction.amount
            
            # 增加接收方余额
            if transaction.receiver not in self.balances:
                self.balances[transaction.receiver] = 0
            self.balances[transaction.receiver] += transaction.amount
    
    def get_balance(self, address: str) -> float:
        """获取账户余额"""
        return self.storage_manager.get_balance(address)
    
    def get_all_balances(self) -> Dict[str, float]:
        """获取所有账户余额"""
        return self.storage_manager.get_all_balances()
    
    def is_chain_valid(self) -> bool:
        """验证区块链完整性"""
        try:
            latest_height = self.storage_manager.get_latest_block_height()
            
            for height in range(1, latest_height + 1):
                current_block = self.storage_manager.get_block_by_height(height)
                previous_block = self.storage_manager.get_block_by_height(height - 1)
                
                if not current_block or not previous_block:
                    return False
                
                # 验证哈希连接
                if current_block.previous_hash != previous_block.hash:
                    return False
                
                # 验证区块哈希
                if current_block.hash != current_block.calculate_hash():
                    return False
            
            return True
            
        except Exception as e:
            print(f"验证区块链失败: {e}")
            return False
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[tuple]:
        """根据哈希获取交易"""
        return self.storage_manager.get_transaction_by_hash(tx_hash)
    
    def get_chain_info(self) -> Dict[str, Any]:
        """获取区块链信息"""
        latest_height = self.storage_manager.get_latest_block_height()
        latest_block = self.get_latest_block()
        
        return {
            'height': latest_height,
            'latest_block_hash': latest_block.hash if latest_block else None,
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'pending_transactions': len(self.pending_transactions),
            'total_accounts': len(self.balances),
            'is_valid': self.is_chain_valid(),
            'storage_stats': self.storage_manager.get_storage_stats()
        }
    
    def export_chain_data(self, export_path: str) -> bool:
        """导出区块链数据"""
        return self.storage_manager.export_blockchain_data(export_path)
    
    def import_chain_data(self, import_path: str) -> bool:
        """导入区块链数据"""
        success = self.storage_manager.import_blockchain_data(import_path)
        if success:
            # 重新加载状态
            self._load_from_storage()
        return success
    
    def cleanup_old_data(self, keep_blocks: int = 1000) -> bool:
        """清理旧数据"""
        return self.storage_manager.cleanup_old_data(keep_blocks)
    
    def close(self):
        """关闭区块链"""
        self._save_to_storage()
        self.storage_manager.close()
        print("✅ 区块链已关闭")
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Tuple[Transaction, int]]:
        """根据ID获取交易及其所在区块索引"""
        for block in self.chain:
            transaction = block.get_transaction_by_id(transaction_id)
            if transaction:
                return transaction, block.index
        return None
    
    def get_transactions_by_address(self, address: str) -> List[Tuple[Transaction, int]]:
        """获取地址相关的所有交易"""
        transactions = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == address or transaction.receiver == address:
                    transactions.append((transaction, block.index))
        return transactions
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """获取区块链统计信息"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        total_fees = sum(block.get_transaction_fees() for block in self.chain)
        
        return {
            'total_blocks': len(self.chain),
            'total_transactions': total_transactions,
            'total_fees': total_fees,
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'pending_transactions': len(self.pending_transactions),
            'latest_block_hash': self.get_latest_block().hash if self.get_latest_block() else None,
            'chain_valid': self.is_chain_valid()
        }
    
    def adjust_difficulty(self) -> None:
        """调整挖矿难度"""
        if len(self.chain) < 2:
            return
        
        # 计算最近区块的挖矿时间
        latest_block = self.get_latest_block()
        previous_block = self.chain[-2]
        
        time_taken = latest_block.timestamp - previous_block.timestamp
        target_time = 10  # 目标10秒一个区块
        
        if time_taken < target_time / 2:
            self.difficulty += 1
            print(f"难度增加到: {self.difficulty}")
        elif time_taken > target_time * 2:
            self.difficulty = max(1, self.difficulty - 1)
            print(f"难度降低到: {self.difficulty}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'chain': [block.to_dict() for block in self.chain],
            'balances': self.balances,
            'stats': self.get_chain_info()
        }
    
    def save_to_file(self, filename: str) -> None:
        """保存区块链到文件"""
        data = self.to_dict()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"区块链已保存到: {filename}")
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Blockchain':
        """从文件加载区块链"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        blockchain = cls(difficulty=data['difficulty'], mining_reward=data['mining_reward'])
        
        # 重建链
        blockchain.chain = []
        for block_data in data['chain']:
            block = Block.from_dict(block_data)
            blockchain.chain.append(block)
        
        # 恢复余额
        blockchain.balances = data['balances']
        
        print(f"区块链已从文件加载: {filename}")
        return blockchain 