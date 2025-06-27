"""
区块相关类
"""
import time
import json
from typing import List, Dict, Any, Optional
from .transaction import Transaction
from ..utils.crypto import CryptoUtils
from ..utils.merkle import MerkleTree


class Block:
    """区块类"""
    
    def __init__(self, index: int, transactions: List[Transaction], 
                 previous_hash: str, miner_address: str = ""):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.miner_address = miner_address
        
        # 构建Merkle树
        transaction_data = [tx.to_json() for tx in transactions]
        self.merkle_tree = MerkleTree(transaction_data)
        self.merkle_root = self.merkle_tree.root or ""
        
        # 挖矿相关
        self.nonce = 0
        self.difficulty = 4
        self.hash = ""
        
        # 计算初始哈希
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """计算区块哈希"""
        block_string = (f"{self.index}{self.timestamp}{self.merkle_root}"
                       f"{self.previous_hash}{self.nonce}{self.miner_address}")
        return CryptoUtils.hash_data(block_string)
    
    def mine_block(self, difficulty: int) -> None:
        """挖矿"""
        self.difficulty = difficulty
        target = "0" * difficulty
        
        print(f"开始挖矿区块 #{self.index}，难度: {difficulty}")
        start_time = time.time()
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self._calculate_hash()
            
            # 每100000次尝试输出一次进度
            if self.nonce % 100000 == 0:
                print(f"尝试次数: {self.nonce}，当前哈希: {self.hash[:20]}...")
        
        end_time = time.time()
        mining_time = end_time - start_time
        
        print(f"区块 #{self.index} 挖矿成功！")
        print(f"哈希值: {self.hash}")
        print(f"Nonce: {self.nonce}")
        print(f"挖矿用时: {mining_time:.2f} 秒")
        print("-" * 60)
    
    def is_valid(self) -> bool:
        """验证区块有效性"""
        # 验证哈希
        if self.hash != self._calculate_hash():
            return False
        
        # 验证工作量证明
        if not self.hash.startswith("0" * self.difficulty):
            return False
        
        # 验证所有交易
        for transaction in self.transactions:
            if not transaction.is_valid():
                return False
        
        # 验证Merkle根
        transaction_data = [tx.to_json() for tx in self.transactions]
        merkle_tree = MerkleTree(transaction_data)
        if merkle_tree.root != self.merkle_root:
            return False
        
        return True
    
    def get_transaction_fees(self) -> float:
        """获取区块中所有交易的手续费总和"""
        return sum(tx.fee for tx in self.transactions)
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """根据ID获取交易"""
        for tx in self.transactions:
            if tx.transaction_id == transaction_id:
                return tx
        return None
    
    def verify_transaction_in_block(self, transaction_id: str) -> bool:
        """验证交易是否在区块中（使用Merkle树）"""
        for i, tx in enumerate(self.transactions):
            if tx.transaction_id == transaction_id:
                merkle_path = self.merkle_tree.get_merkle_path(i)
                return self.merkle_tree.verify_transaction(tx.to_json(), i, merkle_path)
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'transaction_count': len(self.transactions),
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'miner_address': self.miner_address,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'hash': self.hash,
            'total_fees': self.get_transaction_fees()
        }
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """从字典创建区块"""
        transactions = [Transaction.from_dict(tx_data) for tx_data in data['transactions']]
        
        block = cls(
            index=data['index'],
            transactions=transactions,
            previous_hash=data['previous_hash'],
            miner_address=data.get('miner_address', "")
        )
        
        # 恢复其他属性
        block.timestamp = data['timestamp']
        block.merkle_root = data['merkle_root']
        block.nonce = data['nonce']
        block.difficulty = data['difficulty']
        block.hash = data['hash']
        
        return block
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Block':
        """从JSON创建区块"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class GenesisBlock(Block):
    """创世区块类"""
    
    def __init__(self, miner_address: str = "genesis"):
        # 创建创世交易
        genesis_transaction = Transaction(
            sender="genesis",
            receiver=miner_address,
            amount=1000000,  # 初始代币数量
            fee=0,
            data="Genesis block transaction"
        )
        
        super().__init__(
            index=0,
            transactions=[genesis_transaction],
            previous_hash="0" * 64,
            miner_address=miner_address
        )
        
        # 创世区块不需要挖矿，直接设置哈希
        self.hash = self._calculate_hash() 