#!/usr/bin/env python3
"""
区块链节点启动脚本
"""
import sys
import os
import click
import json
from pathlib import Path
import threading
import time

# 添加src目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from core.blockchain import Blockchain
from network.api import BlockchainAPI
from network.node import P2PNode
from utils.crypto import Wallet
from config import settings


@click.command()
@click.option('--port', default=5000, help='API服务端口')
@click.option('--host', default='0.0.0.0', help='API服务主机')
@click.option('--peers', help='对等节点列表 (逗号分隔)')
@click.option('--difficulty', default=4, help='挖矿难度')
@click.option('--mining-reward', default=50.0, help='挖矿奖励')
@click.option('--auto-mine', is_flag=True, help='自动挖矿模式')
@click.option('--mining-interval', default=10, help='挖矿间隔(秒)')
@click.option('--storage-type', default='leveldb', 
              type=click.Choice(['leveldb', 'distributed']),
              help='存储类型')
@click.option('--storage-path', default='./blockchain_data', help='存储路径')
@click.option('--compression', default='snappy',
              type=click.Choice(['snappy', 'lz4', 'none']),
              help='压缩算法')
@click.option('--replication-factor', default=2, help='分布式存储复制因子')
@click.option('--consistency-level', default='quorum',
              type=click.Choice(['strong', 'quorum', 'eventual']),
              help='分布式存储一致性级别')
def start_node(port, host, peers, difficulty, mining_reward, auto_mine, 
               mining_interval, storage_type, storage_path, compression,
               replication_factor, consistency_level):
    """启动区块链节点"""
    
    print(f"🚀 启动区块链节点")
    print(f"   端口: {port}")
    print(f"   存储类型: {storage_type}")
    print(f"   存储路径: {storage_path}")
    print(f"   压缩算法: {compression}")
    
    try:
        # 配置存储
        storage_config = {
            'type': storage_type,
            'path': storage_path,
            'compression': compression if compression != 'none' else None
        }
        
        # 如果是分布式存储，添加分布式配置
        if storage_type == 'distributed':
            peer_list = []
            if peers:
                peer_list = [f"http://{peer.strip()}" for peer in peers.split(',')]
            
            storage_config['distributed'] = {
                'peers': peer_list,
                'replication_factor': replication_factor,
                'consistency_level': consistency_level
            }
            
            print(f"   对等节点: {len(peer_list)}")
            print(f"   复制因子: {replication_factor}")
            print(f"   一致性级别: {consistency_level}")
        
        # 初始化区块链
        blockchain = Blockchain(
            difficulty=difficulty,
            mining_reward=mining_reward,
            storage_config=storage_config
        )
        
        # 创建钱包
        wallet = Wallet()
        print(f"💳 节点钱包地址: {wallet.address}")
        
        # 初始化API
        api = BlockchainAPI(blockchain, port)
        
        # 初始化网络节点
        if peers:
            peer_list = [f"http://{peer.strip()}:{port}" for peer in peers.split(',')]
            network_node = NetworkNode(blockchain, port, peer_list)
            
            # 启动网络同步
            network_thread = threading.Thread(target=network_node.start, daemon=True)
            network_thread.start()
            
            print(f"🌐 网络节点已启动，连接到 {len(peer_list)} 个对等节点")
        
        # 自动挖矿
        if auto_mine:
            def auto_mining():
                while True:
                    try:
                        time.sleep(mining_interval)
                        if blockchain.pending_transactions:
                            block = blockchain.mine_pending_transactions(wallet.address)
                            if block:
                                print(f"⛏️  自动挖矿成功 - 区块 {block.index}")
                                # 同步存储状态
                                stats = blockchain.storage_manager.get_storage_stats()
                                print(f"📊 存储状态: 高度={stats.get('latest_block_height', 0)}, "
                                      f"大小={stats.get('estimated_size_mb', 0)}MB")
                    except Exception as e:
                        print(f"❌ 自动挖矿错误: {e}")
            
            mining_thread = threading.Thread(target=auto_mining, daemon=True)
            mining_thread.start()
            print(f"⛏️  自动挖矿已启动 (间隔: {mining_interval}秒)")
        
        # 启动API服务器
        print(f"🌐 API服务器启动中...")
        print(f"   访问地址: http://{host}:{port}")
        print(f"   存储管理: http://{host}:{port}/api/v1/storage/stats")
        print(f"   使用 Ctrl+C 停止服务")
        
        api.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        print("\n⏹️  节点被用户停止")
    except Exception as e:
        print(f"\n❌ 节点启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if 'blockchain' in locals():
            blockchain.close()
        print("✅ 节点已关闭")


@click.command()
@click.option('--name', prompt='钱包名称', help='钱包名称')
def create_wallet(name):
    """创建新钱包"""
    wallet = Wallet()
    
    # 创建钱包目录
    wallet_dir = Path(project_root) / "wallets"
    wallet_dir.mkdir(exist_ok=True)
    
    # 保存钱包
    wallet_file = wallet_dir / f"{name}.json"
    with open(wallet_file, 'w') as f:
        json.dump(wallet.to_dict(), f, indent=2)
    
    print("=" * 60)
    print("💰 新钱包已创建")
    print("=" * 60)
    print(f"地址: {wallet.address}")
    print(f"公钥: {wallet.public_key}")
    print(f"私钥: {wallet.private_key}")
    print(f"文件: {wallet_file}")
    print("=" * 60)
    print("⚠️  警告: 请安全保管私钥，不要泄露给他人！")


@click.group()
def cli():
    """区块链节点管理工具"""
    pass


cli.add_command(start_node)
cli.add_command(create_wallet)


if __name__ == '__main__':
    cli() 