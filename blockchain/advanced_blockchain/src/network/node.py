"""
P2P网络节点
"""
import json
import requests
import threading
import time
from typing import List, Dict, Any, Optional
from ..core.blockchain import Blockchain
from ..core.transaction import Transaction
from ..core.block import Block
from ..config import settings


class P2PNode:
    """P2P网络节点"""
    
    def __init__(self, host: str, port: int, blockchain: Blockchain):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers: List[Dict[str, Any]] = []
        self.running = False
        self.sync_thread = None
        
    def add_peer(self, peer_host: str, peer_port: int) -> bool:
        """添加对等节点"""
        peer = {'host': peer_host, 'port': peer_port}
        
        # 检查是否已存在
        for existing_peer in self.peers:
            if existing_peer['host'] == peer_host and existing_peer['port'] == peer_port:
                return False
        
        # 测试连接
        if self._test_peer_connection(peer):
            self.peers.append(peer)
            print(f"已添加对等节点: {peer_host}:{peer_port}")
            return True
        else:
            print(f"无法连接到对等节点: {peer_host}:{peer_port}")
            return False
    
    def _test_peer_connection(self, peer: Dict[str, Any]) -> bool:
        """测试对等节点连接"""
        try:
            url = f"http://{peer['host']}:{peer['port']}{settings.API_PREFIX}/status"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def broadcast_transaction(self, transaction: Transaction) -> None:
        """广播交易到所有对等节点"""
        transaction_data = transaction.to_dict()
        
        for peer in self.peers:
            try:
                url = f"http://{peer['host']}:{peer['port']}{settings.API_PREFIX}/transactions"
                
                # 将交易数据转换为API格式
                api_data = {
                    'sender': transaction.sender,
                    'receiver': transaction.receiver,
                    'amount': transaction.amount,
                    'fee': transaction.fee,
                    'data': transaction.data,
                    'signature': transaction.signature,
                    'public_key': transaction.public_key
                }
                
                requests.post(url, json=api_data, timeout=5)
                print(f"交易已广播到: {peer['host']}:{peer['port']}")
                
            except Exception as e:
                print(f"广播交易到 {peer['host']}:{peer['port']} 失败: {e}")
    
    def broadcast_block(self, block: Block) -> None:
        """广播区块到所有对等节点"""
        block_data = block.to_dict()
        
        for peer in self.peers:
            try:
                url = f"http://{peer['host']}:{peer['port']}{settings.API_PREFIX}/blocks"
                requests.post(url, json=block_data, timeout=10)
                print(f"区块已广播到: {peer['host']}:{peer['port']}")
                
            except Exception as e:
                print(f"广播区块到 {peer['host']}:{peer['port']} 失败: {e}")
    
    def sync_blockchain(self) -> None:
        """同步区块链"""
        if not self.peers:
            return
        
        # 获取最长链
        longest_chain = None
        longest_length = len(self.blockchain.chain)
        
        for peer in self.peers:
            try:
                url = f"http://{peer['host']}:{peer['port']}{settings.API_PREFIX}/blocks"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    peer_blocks = data.get('blocks', [])
                    
                    if len(peer_blocks) > longest_length:
                        longest_chain = peer_blocks
                        longest_length = len(peer_blocks)
                        
            except Exception as e:
                print(f"从 {peer['host']}:{peer['port']} 同步失败: {e}")
        
        # 如果发现更长的链，进行同步
        if longest_chain:
            self._update_blockchain(longest_chain)
    
    def _update_blockchain(self, new_chain_data: List[Dict[str, Any]]) -> None:
        """更新区块链"""
        try:
            # 验证新链
            temp_blockchain = Blockchain(difficulty=self.blockchain.difficulty)
            temp_blockchain.chain = []
            
            for block_data in new_chain_data:
                block = Block.from_dict(block_data)
                temp_blockchain.chain.append(block)
            
            # 验证链的有效性
            if temp_blockchain.is_chain_valid():
                # 备份当前链
                old_chain = self.blockchain.chain.copy()
                
                # 更新链
                self.blockchain.chain = temp_blockchain.chain
                
                # 重新计算余额
                self.blockchain.balances = {}
                for block in self.blockchain.chain:
                    self.blockchain._update_balances_from_block(block)
                
                print(f"区块链已同步，新长度: {len(self.blockchain.chain)}")
            else:
                print("接收到的链验证失败，拒绝同步")
                
        except Exception as e:
            print(f"更新区块链失败: {e}")
    
    def discover_peers(self) -> None:
        """发现新的对等节点"""
        known_peers = self.peers.copy()
        
        for peer in known_peers:
            try:
                url = f"http://{peer['host']}:{peer['port']}{settings.API_PREFIX}/peers"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    peer_list = response.json().get('peers', [])
                    
                    for new_peer in peer_list:
                        if len(self.peers) < settings.MAX_PEERS:
                            self.add_peer(new_peer['host'], new_peer['port'])
                            
            except Exception as e:
                print(f"从 {peer['host']}:{peer['port']} 发现节点失败: {e}")
    
    def start_sync_thread(self) -> None:
        """启动同步线程"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        print("同步线程已启动")
    
    def stop_sync_thread(self) -> None:
        """停止同步线程"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join()
        print("同步线程已停止")
    
    def _sync_loop(self) -> None:
        """同步循环"""
        while self.running:
            try:
                # 同步区块链
                self.sync_blockchain()
                
                # 发现新节点
                if len(self.peers) < settings.MAX_PEERS:
                    self.discover_peers()
                
                # 等待下次同步
                time.sleep(settings.SYNC_INTERVAL)
                
            except Exception as e:
                print(f"同步循环错误: {e}")
                time.sleep(5)
    
    def get_peer_info(self) -> Dict[str, Any]:
        """获取节点信息"""
        return {
            'host': self.host,
            'port': self.port,
            'peers': self.peers,
            'peer_count': len(self.peers),
            'blockchain_height': len(self.blockchain.chain),
            'running': self.running
        } 