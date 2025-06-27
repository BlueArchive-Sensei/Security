import hashlib
import json
import time
from datetime import datetime

class Block:
    """
    区块类 - 区块链中的基本单元
    
    每个区块包含：
    - index: 区块索引（在链中的位置）
    - timestamp: 区块创建时间戳
    - data: 区块中存储的数据（交易信息等）
    - previous_hash: 前一个区块的哈希值
    - nonce: 工作量证明中的随机数
    - hash: 当前区块的哈希值
    """
    
    def __init__(self, index, data, previous_hash):
        """
        初始化区块
        
        Args:
            index (int): 区块索引
            data (str): 区块数据
            previous_hash (str): 前一个区块的哈希值
        """
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0  # 工作量证明的随机数
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        计算区块的哈希值
        
        使用SHA-256算法对区块的所有信息进行哈希计算
        
        Returns:
            str: 区块的哈希值
        """
        # 将区块的所有信息组合成字符串
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        # 使用SHA-256计算哈希值
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        """
        挖矿 - 工作量证明算法
        
        不断尝试不同的nonce值，直到找到满足难度要求的哈希值
        难度要求：哈希值必须以指定数量的0开头
        
        Args:
            difficulty (int): 挖矿难度（哈希值开头0的个数）
        """
        print(f"开始挖矿区块 {self.index}...")
        # 创建目标字符串（difficulty个0）
        target = "0" * difficulty
        
        # 记录开始时间
        start_time = time.time()
        
        # 不断尝试不同的nonce值
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        # 计算挖矿用时
        end_time = time.time()
        mining_time = round(end_time - start_time, 2)
        
        print(f"区块 {self.index} 挖矿成功！")
        print(f"哈希值: {self.hash}")
        print(f"Nonce: {self.nonce}")
        print(f"挖矿用时: {mining_time} 秒")
        print("-" * 50)
    
    def to_dict(self):
        """
        将区块信息转换为字典格式
        
        Returns:
            dict: 区块信息字典
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class Blockchain:
    """
    区块链类 - 管理整个区块链
    
    功能包括：
    - 创建创世区块
    - 添加新区块
    - 验证区块链完整性
    - 获取区块链信息
    """
    
    def __init__(self):
        """
        初始化区块链
        
        创建创世区块（第一个区块）并设置挖矿难度
        """
        self.difficulty = 3  # 挖矿难度（哈希值开头0的个数）
        self.chain = [self.create_genesis_block()]
        
    def create_genesis_block(self):
        """
        创建创世区块
        
        创世区块是区块链中的第一个区块，没有前驱区块
        
        Returns:
            Block: 创世区块
        """
        genesis_block = Block(0, "创世区块 - 区块链的起始", "0")
        genesis_block.mine_block(self.difficulty)
        return genesis_block
    
    def get_latest_block(self):
        """
        获取最新的区块
        
        Returns:
            Block: 链中的最后一个区块
        """
        return self.chain[-1]
    
    def add_block(self, new_block):
        """
        向区块链添加新区块
        
        设置新区块的前驱哈希值并进行挖矿
        
        Args:
            new_block (Block): 要添加的新区块
        """
        # 设置新区块的前驱哈希值
        new_block.previous_hash = self.get_latest_block().hash
        # 挖矿
        new_block.mine_block(self.difficulty)
        # 添加到链中
        self.chain.append(new_block)
    
    def create_and_add_block(self, data):
        """
        创建并添加新区块的便捷方法
        
        Args:
            data (str): 区块数据
        """
        # 计算新区块的索引
        new_index = len(self.chain)
        # 创建新区块
        new_block = Block(new_index, data, "")
        # 添加到链中
        self.add_block(new_block)
    
    def is_chain_valid(self):
        """
        验证区块链的完整性
        
        检查每个区块的哈希值是否正确，以及区块间的连接是否有效
        
        Returns:
            bool: 区块链是否有效
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # 检查当前区块的哈希值是否正确
            if current_block.hash != current_block.calculate_hash():
                print(f"区块 {i} 的哈希值不正确！")
                return False
            
            # 检查当前区块是否正确链接到前一个区块
            if current_block.previous_hash != previous_block.hash:
                print(f"区块 {i} 与前一个区块的链接不正确！")
                return False
        
        return True
    
    def get_blockchain_info(self):
        """
        获取区块链的详细信息
        
        Returns:
            dict: 区块链信息
        """
        return {
            'total_blocks': len(self.chain),
            'difficulty': self.difficulty,
            'is_valid': self.is_chain_valid(),
            'latest_block_hash': self.get_latest_block().hash,
            'chain': [block.to_dict() for block in self.chain]
        }
    
    def print_blockchain(self):
        """
        以友好的格式打印整个区块链
        """
        print("=" * 60)
        print("区块链信息")
        print("=" * 60)
        print(f"区块总数: {len(self.chain)}")
        print(f"挖矿难度: {self.difficulty}")
        print(f"链的有效性: {'有效' if self.is_chain_valid() else '无效'}")
        print("=" * 60)
        
        for block in self.chain:
            print(f"区块 #{block.index}")
            print(f"时间: {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"数据: {block.data}")
            print(f"前驱哈希: {block.previous_hash}")
            print(f"当前哈希: {block.hash}")
            print(f"Nonce: {block.nonce}")
            print("-" * 60)
    
    def save_to_file(self, filename):
        """
        将区块链保存到JSON文件
        
        Args:
            filename (str): 文件名
        """
        blockchain_data = self.get_blockchain_info()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(blockchain_data, f, ensure_ascii=False, indent=2)
        print(f"区块链已保存到文件: {filename}")


class Transaction:
    """
    交易类 - 表示区块链中的交易
    
    在实际的区块链中，区块通常包含多个交易
    """
    
    def __init__(self, sender, receiver, amount):
        """
        初始化交易
        
        Args:
            sender (str): 发送方
            receiver (str): 接收方
            amount (float): 交易金额
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()
    
    def to_string(self):
        """
        将交易转换为字符串表示
        
        Returns:
            str: 交易的字符串表示
        """
        return f"{self.sender} -> {self.receiver}: {self.amount}"
    
    def to_dict(self):
        """
        将交易转换为字典格式
        
        Returns:
            dict: 交易信息字典
        """
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }


class SimpleWallet:
    """
    简单钱包类 - 用于模拟区块链交易
    """
    
    def __init__(self, name, initial_balance=100):
        """
        初始化钱包
        
        Args:
            name (str): 钱包所有者姓名
            initial_balance (float): 初始余额
        """
        self.name = name
        self.balance = initial_balance
        self.transaction_history = []
    
    def send_money(self, receiver, amount):
        """
        发送金钱
        
        Args:
            receiver (str): 接收方
            amount (float): 金额
            
        Returns:
            Transaction: 交易对象，如果余额不足则返回None
        """
        if self.balance >= amount:
            self.balance -= amount
            transaction = Transaction(self.name, receiver, amount)
            self.transaction_history.append(transaction)
            return transaction
        else:
            print(f"余额不足！当前余额: {self.balance}")
            return None
    
    def receive_money(self, sender, amount):
        """
        接收金钱
        
        Args:
            sender (str): 发送方
            amount (float): 金额
        """
        self.balance += amount
        transaction = Transaction(sender, self.name, amount)
        self.transaction_history.append(transaction)
    
    def get_balance(self):
        """
        获取当前余额
        
        Returns:
            float: 当前余额
        """
        return self.balance
    
    def get_transaction_history(self):
        """
        获取交易历史
        
        Returns:
            list: 交易历史列表
        """
        return [tx.to_dict() for tx in self.transaction_history] 