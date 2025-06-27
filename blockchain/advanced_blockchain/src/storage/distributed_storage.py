"""
分布式存储实现
"""
import json
import time
import hashlib
import threading
import requests
from typing import Optional, List, Dict, Any, Iterator
from .storage_interface import StorageInterface

# 尝试导入LevelDB存储，如果不可用则使用SQLite
try:
    from .leveldb_storage import LevelDBStorage
    DEFAULT_STORAGE_CLASS = LevelDBStorage
except ImportError:
    from .sqlite_storage import SQLiteStorage
    DEFAULT_STORAGE_CLASS = SQLiteStorage


class DistributedStorage(StorageInterface):
    """分布式存储实现"""
    
    def __init__(self, local_storage=None, 
                 peer_nodes: List[str] = None,
                 replication_factor: int = 2,
                 consistency_level: str = "quorum"):
        """
        初始化分布式存储
        
        Args:
            local_storage: 本地存储实例（LevelDBStorage或SQLiteStorage）
            peer_nodes: 对等节点列表 ["http://node1:5000", "http://node2:5000"]
            replication_factor: 复制因子
            consistency_level: 一致性级别 ("strong", "quorum", "eventual")
        """
        # 如果没有提供本地存储，使用默认的
        if local_storage is None:
            local_storage = DEFAULT_STORAGE_CLASS()
            
        self.local_storage = local_storage
        self.peer_nodes = peer_nodes or []
        self.replication_factor = min(replication_factor, len(self.peer_nodes) + 1)
        self.consistency_level = consistency_level
        self.lock = threading.RLock()
        
        # 节点健康状态
        self.node_health = {node: True for node in self.peer_nodes}
        
        print(f"✅ 分布式存储已初始化:")
        print(f"   本地节点: {getattr(local_storage, 'db_path', 'unknown')}")
        print(f"   对等节点: {len(self.peer_nodes)}")
        print(f"   复制因子: {self.replication_factor}")
        print(f"   一致性级别: {self.consistency_level}")
    
    def _get_key_hash(self, key: str) -> str:
        """计算键的哈希值，用于分布式路由"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _select_nodes_for_key(self, key: str) -> List[str]:
        """为键选择存储节点"""
        key_hash = self._get_key_hash(key)
        
        # 基于哈希值选择节点
        available_nodes = [node for node in self.peer_nodes 
                          if self.node_health.get(node, False)]
        
        if not available_nodes:
            return []
        
        # 使用一致性哈希选择节点
        selected_nodes = []
        hash_int = int(key_hash, 16)
        
        for i in range(self.replication_factor - 1):  # -1 因为本地节点总是包含
            node_index = (hash_int + i) % len(available_nodes)
            selected_nodes.append(available_nodes[node_index])
        
        return selected_nodes
    
    def _check_node_health(self, node: str) -> bool:
        """检查节点健康状态"""
        try:
            response = requests.get(f"{node}/api/v1/storage/health", timeout=3)
            healthy = response.status_code == 200
            self.node_health[node] = healthy
            return healthy
        except:
            self.node_health[node] = False
            return False
    
    def _replicate_to_peers(self, key: str, value: bytes, operation: str = "put") -> Dict[str, bool]:
        """复制数据到对等节点"""
        results = {}
        selected_nodes = self._select_nodes_for_key(key)
        
        for node in selected_nodes:
            try:
                if not self._check_node_health(node):
                    results[node] = False
                    continue
                
                if operation == "put":
                    # 发送PUT请求
                    import base64
                    data = {
                        'key': key,
                        'value': base64.b64encode(value).decode('utf-8')
                    }
                    response = requests.post(
                        f"{node}/api/v1/storage/put",
                        json=data,
                        timeout=10
                    )
                    results[node] = response.status_code == 200
                    
                elif operation == "delete":
                    # 发送DELETE请求
                    response = requests.delete(
                        f"{node}/api/v1/storage/{key}",
                        timeout=10
                    )
                    results[node] = response.status_code == 200
                    
            except Exception as e:
                print(f"复制到节点 {node} 失败: {e}")
                results[node] = False
                self.node_health[node] = False
        
        return results
    
    def _read_from_peers(self, key: str) -> Optional[bytes]:
        """从对等节点读取数据"""
        selected_nodes = self._select_nodes_for_key(key)
        
        for node in selected_nodes:
            try:
                if not self._check_node_health(node):
                    continue
                
                response = requests.get(
                    f"{node}/api/v1/storage/{key}",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'value' in data:
                        import base64
                        return base64.b64decode(data['value'].encode('utf-8'))
                        
            except Exception as e:
                print(f"从节点 {node} 读取失败: {e}")
                self.node_health[node] = False
        
        return None
    
    # ========== 存储接口实现 ==========
    
    def put(self, key: str, value: bytes) -> bool:
        """分布式存储键值对"""
        with self.lock:
            # 首先存储到本地
            local_success = self.local_storage.put(key, value)
            
            if self.consistency_level == "eventual":
                # 异步复制到其他节点
                threading.Thread(
                    target=self._replicate_to_peers,
                    args=(key, value, "put"),
                    daemon=True
                ).start()
                return local_success
            
            else:
                # 同步复制
                replication_results = self._replicate_to_peers(key, value, "put")
                successful_replications = sum(1 for success in replication_results.values() if success)
                
                if self.consistency_level == "strong":
                    # 强一致性：所有节点都必须成功
                    required_success = len(replication_results)
                elif self.consistency_level == "quorum":
                    # 法定人数：大多数节点成功即可
                    required_success = len(replication_results) // 2 + 1
                else:
                    required_success = 1
                
                return local_success and successful_replications >= required_success
    
    def get(self, key: str) -> Optional[bytes]:
        """分布式获取值"""
        with self.lock:
            # 首先尝试从本地获取
            value = self.local_storage.get(key)
            
            if value is not None:
                return value
            
            # 如果本地没有，尝试从对等节点获取
            if self.peer_nodes:
                peer_value = self._read_from_peers(key)
                
                # 如果从对等节点获取到数据，同步到本地
                if peer_value is not None:
                    self.local_storage.put(key, peer_value)
                    return peer_value
            
            return None
    
    def delete(self, key: str) -> bool:
        """分布式删除键值对"""
        with self.lock:
            # 首先从本地删除
            local_success = self.local_storage.delete(key)
            
            if self.consistency_level == "eventual":
                # 异步删除其他节点
                threading.Thread(
                    target=self._replicate_to_peers,
                    args=(key, b"", "delete"),
                    daemon=True
                ).start()
                return local_success
            
            else:
                # 同步删除
                replication_results = self._replicate_to_peers(key, b"", "delete")
                successful_replications = sum(1 for success in replication_results.values() if success)
                
                if self.consistency_level == "strong":
                    required_success = len(replication_results)
                elif self.consistency_level == "quorum":
                    required_success = len(replication_results) // 2 + 1
                else:
                    required_success = 1
                
                return local_success and successful_replications >= required_success
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None
    
    def batch_put(self, items: Dict[str, bytes]) -> bool:
        """批量存储"""
        # TODO: 优化批量操作的分布式实现
        results = []
        for key, value in items.items():
            results.append(self.put(key, value))
        return all(results)
    
    def batch_delete(self, keys: List[str]) -> bool:
        """批量删除"""
        # TODO: 优化批量操作的分布式实现
        results = []
        for key in keys:
            results.append(self.delete(key))
        return all(results)
    
    def scan(self, prefix: str, limit: int = 100) -> Iterator[tuple]:
        """扫描指定前缀的键值对"""
        # 主要从本地扫描，TODO: 需要实现分布式扫描
        yield from self.local_storage.scan(prefix, limit)
    
    def close(self) -> None:
        """关闭存储连接"""
        self.local_storage.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取分布式存储统计信息"""
        local_stats = self.local_storage.get_stats()
        
        # 添加分布式信息
        cluster_stats = {
            'cluster_info': {
                'peer_nodes': len(self.peer_nodes),
                'healthy_nodes': sum(1 for healthy in self.node_health.values() if healthy),
                'replication_factor': self.replication_factor,
                'consistency_level': self.consistency_level,
                'node_health': self.node_health
            }
        }
        
        local_stats.update(cluster_stats)
        return local_stats
    
    # ========== 分布式管理功能 ==========
    
    def add_peer_node(self, node_url: str) -> bool:
        """添加对等节点"""
        if node_url not in self.peer_nodes:
            self.peer_nodes.append(node_url)
            self.node_health[node_url] = self._check_node_health(node_url)
            print(f"✅ 已添加对等节点: {node_url}")
            return True
        return False
    
    def remove_peer_node(self, node_url: str) -> bool:
        """移除对等节点"""
        if node_url in self.peer_nodes:
            self.peer_nodes.remove(node_url)
            self.node_health.pop(node_url, None)
            print(f"✅ 已移除对等节点: {node_url}")
            return True
        return False
    
    def sync_with_peers(self) -> Dict[str, Any]:
        """与对等节点同步数据"""
        sync_results = {
            'synced_keys': 0,
            'failed_keys': 0,
            'conflicts': 0
        }
        
        # TODO: 实现完整的数据同步逻辑
        # 这里可以实现：
        # 1. 比较各节点的数据版本
        # 2. 同步缺失的数据
        # 3. 解决数据冲突
        
        return sync_results
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        healthy_nodes = []
        unhealthy_nodes = []
        
        for node in self.peer_nodes:
            if self._check_node_health(node):
                healthy_nodes.append(node)
            else:
                unhealthy_nodes.append(node)
        
        return {
            'total_nodes': len(self.peer_nodes) + 1,  # +1 for local
            'healthy_nodes': len(healthy_nodes) + 1,
            'unhealthy_nodes': len(unhealthy_nodes),
            'healthy_node_list': healthy_nodes,
            'unhealthy_node_list': unhealthy_nodes,
            'replication_factor': self.replication_factor,
            'consistency_level': self.consistency_level
        } 