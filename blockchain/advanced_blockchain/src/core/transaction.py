"""
交易相关类
"""
import time
import json
from typing import List, Dict, Any, Optional
from ..utils.crypto import CryptoUtils


class Transaction:
    """交易类"""
    
    def __init__(self, sender: str, receiver: str, amount: float, 
                 fee: float = 0.0, data: str = ""):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        self.data = data
        self.timestamp = time.time()
        self.nonce = CryptoUtils.generate_nonce()
        
        # 计算交易ID
        self.transaction_id = self._calculate_transaction_id()
        
        # 签名相关
        self.signature = ""
        self.public_key = ""
    
    def _calculate_transaction_id(self) -> str:
        """计算交易ID"""
        transaction_string = f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.data}{self.timestamp}{self.nonce}"
        return CryptoUtils.hash_data(transaction_string)
    
    def get_signing_data(self) -> str:
        """获取用于签名的数据"""
        return f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.data}{self.nonce}"
    
    def sign_transaction(self, private_key: str) -> None:
        """签名交易"""
        signing_data = self.get_signing_data()
        self.signature = CryptoUtils.sign_data(signing_data, private_key)
        self.public_key = CryptoUtils.private_key_to_public_key(private_key)
    
    def is_valid(self) -> bool:
        """验证交易有效性"""
        # 基本验证
        if self.amount <= 0:
            return False
        
        if self.fee < 0:
            return False
        
        if not self.sender or not self.receiver:
            return False
        
        # 验证签名
        if self.signature and self.public_key:
            signing_data = self.get_signing_data()
            if not CryptoUtils.verify_signature(signing_data, self.signature, self.public_key):
                return False
            
            # 验证发送者地址与公钥匹配
            expected_address = CryptoUtils.public_key_to_address(self.public_key)
            if expected_address != self.sender:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'transaction_id': self.transaction_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'fee': self.fee,
            'data': self.data,
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'signature': self.signature,
            'public_key': self.public_key
        }
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """从字典创建交易"""
        tx = cls(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount'],
            fee=data.get('fee', 0.0),
            data=data.get('data', "")
        )
        
        # 恢复其他属性
        tx.timestamp = data['timestamp']
        tx.nonce = data['nonce']
        tx.transaction_id = data['transaction_id']
        tx.signature = data.get('signature', "")
        tx.public_key = data.get('public_key', "")
        
        return tx
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Transaction':
        """从JSON创建交易"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class TransactionPool:
    """交易池类"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.pending_transactions: List[Transaction] = []
        self.transaction_map: Dict[str, Transaction] = {}
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """添加交易到池中"""
        # 验证交易
        if not transaction.is_valid():
            return False
        
        # 检查是否已存在
        if transaction.transaction_id in self.transaction_map:
            return False
        
        # 检查池大小
        if len(self.pending_transactions) >= self.max_size:
            # 移除费用最低的交易
            self._remove_lowest_fee_transaction()
        
        # 添加交易
        self.pending_transactions.append(transaction)
        self.transaction_map[transaction.transaction_id] = transaction
        
        # 按费用排序（费用高的在前）
        self.pending_transactions.sort(key=lambda tx: tx.fee, reverse=True)
        
        return True
    
    def get_transactions_for_block(self, max_count: int = 100) -> List[Transaction]:
        """获取用于打包的交易"""
        selected = self.pending_transactions[:max_count]
        
        # 从池中移除已选择的交易
        for tx in selected:
            if tx.transaction_id in self.transaction_map:
                del self.transaction_map[tx.transaction_id]
        
        self.pending_transactions = self.pending_transactions[max_count:]
        
        return selected
    
    def remove_transaction(self, transaction_id: str) -> bool:
        """移除交易"""
        if transaction_id in self.transaction_map:
            transaction = self.transaction_map[transaction_id]
            del self.transaction_map[transaction_id]
            
            if transaction in self.pending_transactions:
                self.pending_transactions.remove(transaction)
            
            return True
        return False
    
    def _remove_lowest_fee_transaction(self) -> None:
        """移除费用最低的交易"""
        if self.pending_transactions:
            lowest_fee_tx = min(self.pending_transactions, key=lambda tx: tx.fee)
            self.remove_transaction(lowest_fee_tx.transaction_id)
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取交易池状态"""
        return {
            'pending_count': len(self.pending_transactions),
            'max_size': self.max_size,
            'total_fees': sum(tx.fee for tx in self.pending_transactions)
        }
    
    def clear(self) -> None:
        """清空交易池"""
        self.pending_transactions.clear()
        self.transaction_map.clear() 