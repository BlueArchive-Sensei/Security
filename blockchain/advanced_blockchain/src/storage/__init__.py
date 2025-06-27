"""
区块链存储层模块
"""

# 尝试导入LevelDB存储，如果不可用则跳过
try:
    from .leveldb_storage import LevelDBStorage
    LEVELDB_AVAILABLE = True
except ImportError:
    LEVELDB_AVAILABLE = False
    LevelDBStorage = None

# 总是可用的存储类型
from .sqlite_storage import SQLiteStorage
from .distributed_storage import DistributedStorage
from .storage_interface import StorageInterface

# 根据可用性决定导出的类
if LEVELDB_AVAILABLE:
    __all__ = ['LevelDBStorage', 'SQLiteStorage', 'DistributedStorage', 'StorageInterface']
else:
    __all__ = ['SQLiteStorage', 'DistributedStorage', 'StorageInterface'] 