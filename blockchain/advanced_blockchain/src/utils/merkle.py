"""
Merkle树实现
"""
import hashlib
from typing import List, Optional, Dict, Any


class MerkleTree:
    """Merkle树类"""
    
    def __init__(self, transactions: List[str]):
        self.transactions = transactions
        self.tree_levels = []
        self.root = self._build_tree()
    
    def _hash_data(self, data: str) -> str:
        """计算数据哈希"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _build_tree(self) -> Optional[str]:
        """构建Merkle树"""
        if not self.transactions:
            return None
        
        # 计算叶子节点
        current_level = [self._hash_data(tx) for tx in self.transactions]
        self.tree_levels.append(current_level[:])
        
        # 构建树的每一层
        while len(current_level) > 1:
            next_level = []
            
            # 如果节点数为奇数，复制最后一个节点
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])
            
            # 两两组合计算父节点
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent_hash = self._hash_data(left + right)
                next_level.append(parent_hash)
            
            current_level = next_level
            self.tree_levels.append(current_level[:])
        
        return current_level[0] if current_level else None
    
    def get_merkle_path(self, transaction_index: int) -> List[Dict[str, Any]]:
        """获取交易的Merkle路径（用于SPV验证）"""
        if transaction_index >= len(self.transactions):
            return []
        
        path = []
        index = transaction_index
        
        # 从叶子节点向上遍历
        for level_idx in range(len(self.tree_levels) - 1):
            current_level = self.tree_levels[level_idx]
            
            # 确定兄弟节点
            if index % 2 == 0:  # 当前是左节点
                sibling_index = index + 1
                position = 'right'
            else:  # 当前是右节点
                sibling_index = index - 1
                position = 'left'
            
            # 添加兄弟节点到路径
            if sibling_index < len(current_level):
                path.append({
                    'hash': current_level[sibling_index],
                    'position': position
                })
            
            # 移动到下一层
            index = index // 2
        
        return path
    
    def verify_transaction(self, transaction: str, transaction_index: int, 
                          merkle_path: List[Dict[str, Any]]) -> bool:
        """验证交易是否在Merkle树中"""
        if not merkle_path:
            return False
        
        current_hash = self._hash_data(transaction)
        
        # 沿着Merkle路径计算根哈希
        for step in merkle_path:
            sibling_hash = step['hash']
            position = step['position']
            
            if position == 'right':
                current_hash = self._hash_data(current_hash + sibling_hash)
            else:
                current_hash = self._hash_data(sibling_hash + current_hash)
        
        return current_hash == self.root
    
    def get_tree_info(self) -> Dict[str, Any]:
        """获取树的信息"""
        return {
            'root': self.root,
            'transaction_count': len(self.transactions),
            'tree_depth': len(self.tree_levels),
            'tree_levels': self.tree_levels
        } 