"""
区块链REST API服务
"""
import json
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from typing import Dict, Any
from ..core.blockchain import Blockchain
from ..core.transaction import Transaction
from ..utils.crypto import Wallet
from ..config import settings
from ..storage.storage_manager import StorageManager
import time


class BlockchainAPI:
    """区块链API类"""
    
    def __init__(self, blockchain: Blockchain, port: int = 5000):
        self.blockchain = blockchain
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = settings.SECRET_KEY
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 存储管理器
        self.storage_manager = blockchain.storage_manager
        
        # 设置路由
        self._setup_routes()
        self._setup_websocket_events()
        self._setup_storage_routes()
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.route(f'{settings.API_PREFIX}/status', methods=['GET'])
        def get_status():
            """获取区块链状态"""
            return jsonify({
                'status': 'active',
                'stats': self.blockchain.get_blockchain_stats(),
                'node_info': {
                    'version': '1.0.0',
                    'node_type': settings.NODE_TYPE
                }
            })
        
        @self.app.route(f'{settings.API_PREFIX}/blocks', methods=['GET'])
        def get_blocks():
            """获取所有区块"""
            blocks = [block.to_dict() for block in self.blockchain.chain]
            return jsonify({
                'blocks': blocks,
                'count': len(blocks)
            })
        
        @self.app.route(f'{settings.API_PREFIX}/blocks/<int:block_index>', methods=['GET'])
        def get_block(block_index):
            """获取指定区块"""
            if block_index >= len(self.blockchain.chain):
                return jsonify({'error': '区块不存在'}), 404
            
            block = self.blockchain.chain[block_index]
            return jsonify(block.to_dict())
        
        @self.app.route(f'{settings.API_PREFIX}/transactions', methods=['POST'])
        def create_transaction():
            """创建新交易"""
            try:
                data = request.get_json()
                
                # 验证必需字段
                required_fields = ['sender', 'receiver', 'amount', 'private_key']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'缺少字段: {field}'}), 400
                
                # 创建交易
                transaction = Transaction(
                    sender=data['sender'],
                    receiver=data['receiver'],
                    amount=float(data['amount']),
                    fee=float(data.get('fee', 0.1)),
                    data=data.get('data', '')
                )
                
                # 签名交易
                transaction.sign_transaction(data['private_key'])
                
                # 添加到区块链
                if self.blockchain.add_transaction(transaction):
                    # 广播交易
                    self.socketio.emit('new_transaction', transaction.to_dict())
                    
                    return jsonify({
                        'success': True,
                        'transaction_id': transaction.transaction_id,
                        'message': '交易已创建并添加到池中'
                    })
                else:
                    return jsonify({'error': '交易添加失败'}), 400
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route(f'{settings.API_PREFIX}/transactions/<transaction_id>', methods=['GET'])
        def get_transaction(transaction_id):
            """获取指定交易"""
            result = self.blockchain.get_transaction_by_id(transaction_id)
            if result:
                transaction, block_index = result
                return jsonify({
                    'transaction': transaction.to_dict(),
                    'block_index': block_index,
                    'confirmations': len(self.blockchain.chain) - block_index - 1
                })
            else:
                return jsonify({'error': '交易不存在'}), 404
        
        @self.app.route(f'{settings.API_PREFIX}/balance/<address>', methods=['GET'])
        def get_balance(address):
            """获取地址余额"""
            balance = self.blockchain.get_balance(address)
            transactions = self.blockchain.get_transactions_by_address(address)
            
            return jsonify({
                'address': address,
                'balance': balance,
                'transaction_count': len(transactions)
            })
        
        @self.app.route(f'{settings.API_PREFIX}/mine', methods=['POST'])
        def mine_block():
            """挖矿"""
            try:
                data = request.get_json()
                miner_address = data.get('miner_address')
                
                if not miner_address:
                    return jsonify({'error': '需要矿工地址'}), 400
                
                # 挖矿
                new_block = self.blockchain.mine_pending_transactions(miner_address)
                
                if new_block:
                    # 广播新区块
                    self.socketio.emit('new_block', new_block.to_dict())
                    
                    return jsonify({
                        'success': True,
                        'block': new_block.to_dict(),
                        'message': f'区块 #{new_block.index} 挖矿成功'
                    })
                else:
                    return jsonify({'error': '没有待处理的交易'}), 400
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route(f'{settings.API_PREFIX}/wallet/new', methods=['POST'])
        def create_wallet():
            """创建新钱包"""
            wallet = Wallet()
            return jsonify({
                'address': wallet.address,
                'public_key': wallet.public_key,
                'private_key': wallet.private_key,
                'warning': '请安全保管私钥，不要泄露给他人'
            })
        
        @self.app.route(f'{settings.API_PREFIX}/validate', methods=['POST'])
        def validate_chain():
            """验证区块链"""
            is_valid = self.blockchain.is_chain_valid()
            return jsonify({
                'valid': is_valid,
                'message': '区块链有效' if is_valid else '区块链无效'
            })
    
    def _setup_websocket_events(self):
        """设置WebSocket事件"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('客户端已连接')
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('客户端已断开连接')
        
        @self.socketio.on('get_status')
        def handle_get_status():
            """获取实时状态"""
            stats = self.blockchain.get_blockchain_stats()
            self.socketio.emit('status_update', stats)
    
    def _setup_storage_routes(self):
        """设置存储相关路由"""
        
        @self.app.route('/api/v1/storage/health', methods=['GET'])
        def storage_health():
            """存储健康检查"""
            try:
                stats = self.storage_manager.get_storage_stats()
                return jsonify({
                    'status': 'healthy',
                    'storage_type': stats.get('storage_type', 'unknown'),
                    'timestamp': time.time()
                })
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': time.time()
                }), 500
        
        @self.app.route('/api/v1/storage/stats', methods=['GET'])
        def storage_stats():
            """获取存储统计信息"""
            try:
                stats = self.storage_manager.get_storage_stats()
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/put', methods=['POST'])
        def storage_put():
            """存储键值对"""
            try:
                data = request.get_json()
                key = data.get('key')
                value = data.get('value')
                
                if not key or not value:
                    return jsonify({
                        'success': False,
                        'error': '缺少key或value参数'
                    }), 400
                
                # 解码base64值
                import base64
                value_bytes = base64.b64decode(value.encode('utf-8'))
                
                success = self.storage_manager.storage.put(key, value_bytes)
                return jsonify({
                    'success': success,
                    'message': '存储成功' if success else '存储失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/<key>', methods=['GET'])
        def storage_get(key):
            """获取存储值"""
            try:
                value = self.storage_manager.storage.get(key)
                
                if value is None:
                    return jsonify({
                        'success': False,
                        'error': '键不存在'
                    }), 404
                
                # 编码为base64
                import base64
                value_encoded = base64.b64encode(value).decode('utf-8')
                
                return jsonify({
                    'success': True,
                    'value': value_encoded
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/<key>', methods=['DELETE'])
        def storage_delete(key):
            """删除存储键值对"""
            try:
                success = self.storage_manager.storage.delete(key)
                return jsonify({
                    'success': success,
                    'message': '删除成功' if success else '删除失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/backup', methods=['POST'])
        def storage_backup():
            """备份存储数据"""
            try:
                data = request.get_json()
                backup_path = data.get('backup_path', f'./backup_{int(time.time())}.json')
                
                success = self.storage_manager.backup_storage(backup_path)
                return jsonify({
                    'success': success,
                    'backup_path': backup_path,
                    'message': '备份成功' if success else '备份失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/restore', methods=['POST'])
        def storage_restore():
            """恢复存储数据"""
            try:
                data = request.get_json()
                backup_path = data.get('backup_path')
                
                if not backup_path:
                    return jsonify({
                        'success': False,
                        'error': '缺少backup_path参数'
                    }), 400
                
                success = self.storage_manager.restore_storage(backup_path)
                return jsonify({
                    'success': success,
                    'message': '恢复成功' if success else '恢复失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/export', methods=['POST'])
        def storage_export():
            """导出区块链数据"""
            try:
                data = request.get_json()
                export_path = data.get('export_path', f'./blockchain_export_{int(time.time())}.json')
                
                success = self.storage_manager.export_blockchain_data(export_path)
                return jsonify({
                    'success': success,
                    'export_path': export_path,
                    'message': '导出成功' if success else '导出失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/import', methods=['POST'])
        def storage_import():
            """导入区块链数据"""
            try:
                data = request.get_json()
                import_path = data.get('import_path')
                
                if not import_path:
                    return jsonify({
                        'success': False,
                        'error': '缺少import_path参数'
                    }), 400
                
                success = self.storage_manager.import_blockchain_data(import_path)
                return jsonify({
                    'success': success,
                    'message': '导入成功' if success else '导入失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/cleanup', methods=['POST'])
        def storage_cleanup():
            """清理旧数据"""
            try:
                data = request.get_json()
                keep_blocks = data.get('keep_blocks', 1000)
                
                success = self.storage_manager.cleanup_old_data(keep_blocks)
                return jsonify({
                    'success': success,
                    'message': f'清理完成，保留最近{keep_blocks}个区块' if success else '清理失败'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # 分布式存储相关接口
        @self.app.route('/api/v1/storage/cluster/status', methods=['GET'])
        def cluster_status():
            """获取集群状态"""
            try:
                if hasattr(self.storage_manager.storage, 'get_cluster_status'):
                    status = self.storage_manager.storage.get_cluster_status()
                    return jsonify({
                        'success': True,
                        'data': status
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '当前存储不支持集群模式'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/cluster/add-peer', methods=['POST'])
        def add_peer():
            """添加对等节点"""
            try:
                data = request.get_json()
                peer_url = data.get('peer_url')
                
                if not peer_url:
                    return jsonify({
                        'success': False,
                        'error': '缺少peer_url参数'
                    }), 400
                
                if hasattr(self.storage_manager.storage, 'add_peer_node'):
                    success = self.storage_manager.storage.add_peer_node(peer_url)
                    return jsonify({
                        'success': success,
                        'message': f'节点{peer_url}添加{"成功" if success else "失败"}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '当前存储不支持集群模式'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/storage/cluster/remove-peer', methods=['POST'])
        def remove_peer():
            """移除对等节点"""
            try:
                data = request.get_json()
                peer_url = data.get('peer_url')
                
                if not peer_url:
                    return jsonify({
                        'success': False,
                        'error': '缺少peer_url参数'
                    }), 400
                
                if hasattr(self.storage_manager.storage, 'remove_peer_node'):
                    success = self.storage_manager.storage.remove_peer_node(peer_url)
                    return jsonify({
                        'success': success,
                        'message': f'节点{peer_url}移除{"成功" if success else "失败"}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '当前存储不支持集群模式'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """启动API服务"""
        print(f"启动区块链API服务: http://{host}:{port}")
        print(f"WebSocket服务已启用")
        print(f"API端点前缀: {settings.API_PREFIX}")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug) 