#!/usr/bin/env python3
"""
高级区块链系统演示脚本
"""
import sys
import time
import json
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from core.blockchain import Blockchain
from core.transaction import Transaction
from utils.crypto import Wallet
from network.api import BlockchainAPI
import threading


def print_separator(title="", char="=", length=60):
    """打印分隔符"""
    print(f"\n{char * length}")
    if title:
        print(f"{title:^{length}}")
        print(char * length)


def demo_crypto_features():
    """演示加密功能"""
    print_separator("🔐 密码学功能演示")
    
    # 创建钱包
    print("1. 创建数字钱包...")
    alice_wallet = Wallet()
    bob_wallet = Wallet()
    
    print(f"Alice地址: {alice_wallet.address}")
    print(f"Bob地址: {bob_wallet.address}")
    
    # 创建并签名交易
    print("\n2. 创建并签名交易...")
    transaction = Transaction(
        sender=alice_wallet.address,
        receiver=bob_wallet.address,
        amount=100.0,
        fee=1.0,
        data="测试交易"
    )
    
    # 签名交易
    transaction.sign_transaction(alice_wallet.private_key)
    print(f"交易ID: {transaction.transaction_id}")
    print(f"签名: {transaction.signature[:50]}...")
    print(f"交易验证: {'✅ 有效' if transaction.is_valid() else '❌ 无效'}")
    
    return alice_wallet, bob_wallet, transaction


def demo_blockchain_core():
    """演示区块链核心功能"""
    print_separator("⛓️ 区块链核心功能演示")
    
    # 创建区块链
    print("1. 创建区块链...")
    blockchain = Blockchain(difficulty=2)  # 使用较低难度用于演示
    
    # 创建钱包
    alice_wallet = Wallet()
    bob_wallet = Wallet()
    miner_wallet = Wallet()
    
    print(f"创世区块哈希: {blockchain.get_latest_block().hash}")
    print(f"初始余额 - Alice: {blockchain.get_balance(alice_wallet.address)}")
    print(f"初始余额 - Genesis: {blockchain.get_balance('genesis')}")
    
    # 从创世账户给Alice转账
    print("\n2. 创建初始交易...")
    initial_tx = Transaction(
        sender="genesis",
        receiver=alice_wallet.address,
        amount=1000.0,
        fee=0.0,
        data="初始资金分配"
    )
    blockchain.add_transaction(initial_tx)
    
    # 挖矿
    print("\n3. 挖矿处理交易...")
    new_block = blockchain.mine_pending_transactions(miner_wallet.address)
    
    if new_block:
        print(f"新区块已创建: #{new_block.index}")
        print(f"区块哈希: {new_block.hash}")
        print(f"交易数量: {len(new_block.transactions)}")
        
        # 更新后的余额
        print(f"\n4. 更新后的余额:")
        print(f"Alice: {blockchain.get_balance(alice_wallet.address)}")
        print(f"矿工: {blockchain.get_balance(miner_wallet.address)}")
    
    # Alice向Bob转账
    print("\n5. Alice向Bob转账...")
    transfer_tx = Transaction(
        sender=alice_wallet.address,
        receiver=bob_wallet.address,
        amount=200.0,
        fee=2.0,
        data="朋友间转账"
    )
    transfer_tx.sign_transaction(alice_wallet.private_key)
    
    if blockchain.add_transaction(transfer_tx):
        print("✅ 交易已添加到交易池")
        
        # 再次挖矿
        print("\n6. 挖矿处理新交易...")
        second_block = blockchain.mine_pending_transactions(miner_wallet.address)
        
        if second_block:
            print(f"第二个区块已创建: #{second_block.index}")
            print(f"\n7. 最终余额:")
            print(f"Alice: {blockchain.get_balance(alice_wallet.address)}")
            print(f"Bob: {blockchain.get_balance(bob_wallet.address)}")
            print(f"矿工: {blockchain.get_balance(miner_wallet.address)}")
    
    return blockchain, alice_wallet, bob_wallet, miner_wallet


def demo_merkle_tree():
    """演示Merkle树功能"""
    print_separator("🌲 Merkle树功能演示")
    
    # 创建一些虚拟交易
    transactions = [
        "交易1: Alice -> Bob: 100",
        "交易2: Bob -> Charlie: 50", 
        "交易3: Charlie -> David: 25",
        "交易4: David -> Eve: 10"
    ]
    
    print("1. 构建Merkle树...")
    from utils.merkle import MerkleTree
    merkle_tree = MerkleTree(transactions)
    
    print(f"Merkle根: {merkle_tree.root}")
    print(f"交易数量: {len(transactions)}")
    print(f"树深度: {len(merkle_tree.tree_levels)}")
    
    # SPV验证演示
    print("\n2. SPV验证演示...")
    transaction_index = 1
    transaction = transactions[transaction_index]
    merkle_path = merkle_tree.get_merkle_path(transaction_index)
    
    print(f"验证交易: {transaction}")
    print(f"Merkle路径长度: {len(merkle_path)}")
    
    is_valid = merkle_tree.verify_transaction(transaction, transaction_index, merkle_path)
    print(f"SPV验证结果: {'✅ 有效' if is_valid else '❌ 无效'}")


def demo_transaction_pool():
    """演示交易池功能"""
    print_separator("🏊‍♀️ 交易池功能演示")
    
    from core.transaction import TransactionPool
    
    # 创建交易池
    print("1. 创建交易池...")
    tx_pool = TransactionPool(max_size=100)
    
    # 创建多个交易
    print("\n2. 添加多个交易...")
    transactions = []
    for i in range(5):
        tx = Transaction(
            sender=f"user{i}",
            receiver=f"user{i+1}",
            amount=100 + i * 10,
            fee=1 + i * 0.5,  # 不同的手续费
            data=f"交易 #{i+1}"
        )
        transactions.append(tx)
        tx_pool.add_transaction(tx)
        print(f"添加交易 #{i+1}, 手续费: {tx.fee}")
    
    print(f"\n3. 交易池状态:")
    status = tx_pool.get_pool_status()
    print(f"待处理交易数: {status['pending_count']}")
    print(f"总手续费: {status['total_fees']}")
    
    # 获取高优先级交易
    print("\n4. 获取高优先级交易...")
    selected_txs = tx_pool.get_transactions_for_block(max_count=3)
    print("选中的交易 (按优先级排序):")
    for i, tx in enumerate(selected_txs):
        print(f"  {i+1}. 金额: {tx.amount}, 手续费: {tx.fee}")


def demo_api_server():
    """演示API服务器"""
    print_separator("🌐 API服务器演示")
    
    # 创建区块链
    blockchain = Blockchain(difficulty=1)
    
    # 创建API服务器
    print("1. 启动API服务器...")
    api = BlockchainAPI(blockchain)
    
    print("API服务器已创建，包含以下端点:")
    endpoints = [
        "GET  /api/v1/status - 获取节点状态",
        "GET  /api/v1/blocks - 获取所有区块",
        "POST /api/v1/transactions - 创建交易",
        "GET  /api/v1/balance/{address} - 查询余额",
        "POST /api/v1/mine - 挖矿",
        "POST /api/v1/wallet/new - 创建钱包"
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")
    
    print("\n💡 可以使用以下命令启动完整的API服务器:")
    print("   python scripts/start_node.py --auto-mine")


def demo_security_features():
    """演示安全功能"""
    print_separator("🛡️ 安全功能演示")
    
    # 创建区块链
    blockchain = Blockchain(difficulty=1)
    
    print("1. 验证区块链完整性...")
    is_valid = blockchain.is_chain_valid()
    print(f"区块链验证结果: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    # 模拟篡改攻击
    print("\n2. 模拟数据篡改攻击...")
    if len(blockchain.chain) > 0:
        # 尝试修改创世区块
        original_data = blockchain.chain[0].transactions[0].amount
        blockchain.chain[0].transactions[0].amount = 999999  # 篡改金额
        
        print(f"原始金额: {original_data}")
        print(f"篡改后金额: {blockchain.chain[0].transactions[0].amount}")
        
        # 重新验证
        is_valid_after_tampering = blockchain.is_chain_valid()
        print(f"篡改后验证结果: {'✅ 有效' if is_valid_after_tampering else '❌ 无效'}")
        
        # 恢复原始数据
        blockchain.chain[0].transactions[0].amount = original_data
        print("✅ 数据已恢复")


def demo_storage_features():
    """演示存储功能"""
    print("\n" + "="*60)
    print("🗄️  存储层功能演示")
    print("="*60)
    
    # 集中式存储配置
    centralized_config = {
        'type': 'leveldb',
        'path': './demo_centralized_storage',
        'compression': 'snappy'
    }
    
    # 分布式存储配置
    distributed_config = {
        'type': 'distributed',
        'path': './demo_distributed_storage',
        'compression': 'snappy',
        'distributed': {
            'peers': [],  # 演示时为空
            'replication_factor': 1,
            'consistency_level': 'quorum'
        }
    }
    
    print("\n1. 测试集中式存储 (LevelDB)")
    centralized_blockchain = Blockchain(storage_config=centralized_config)
    
    # 创建一些测试交易
    wallet1 = Wallet()
    wallet2 = Wallet()
    
    # 给wallet1一些初始余额
    centralized_blockchain.balances[wallet1.address] = 100.0
    
    # 创建交易
    tx1 = Transaction(wallet1.address, wallet2.address, 30.0)
    tx1.sign_transaction(wallet1.private_key)
    centralized_blockchain.add_transaction(tx1)
    
    # 挖矿
    mined_block = centralized_blockchain.mine_pending_transactions(wallet1.address)
    print(f"✅ 挖矿成功，区块高度: {mined_block.index}")
    
    # 获取存储统计
    stats = centralized_blockchain.storage_manager.get_storage_stats()
    print(f"📊 存储统计: {stats}")
    
    print("\n2. 测试数据导出/导入")
    export_path = "./demo_export.json"
    success = centralized_blockchain.export_chain_data(export_path)
    print(f"{'✅' if success else '❌'} 数据导出: {export_path}")
    
    # 创建新的区块链实例并导入数据
    new_blockchain = Blockchain(storage_config={
        'type': 'leveldb',
        'path': './demo_import_storage',
        'compression': 'snappy'
    })
    
    success = new_blockchain.import_chain_data(export_path)
    print(f"{'✅' if success else '❌'} 数据导入成功")
    
    print("\n3. 测试分布式存储配置")
    distributed_blockchain = Blockchain(storage_config=distributed_config)
    print(f"✅ 分布式区块链初始化完成")
    
    # 清理
    centralized_blockchain.close()
    new_blockchain.close()  
    distributed_blockchain.close()


def main():
    """主演示函数"""
    print("🚀 高级区块链系统演示")
    print("="*60)
    
    try:
        # 1. 密码学功能演示
        demo_crypto_features()
        input("\n按回车键继续下一个演示...")
        
        # 2. 区块链核心功能演示
        blockchain, alice, bob, miner = demo_blockchain_core()
        input("\n按回车键继续下一个演示...")
        
        # 3. Merkle树演示
        demo_merkle_tree()
        input("\n按回车键继续下一个演示...")
        
        # 4. 交易池演示
        demo_transaction_pool()
        input("\n按回车键继续下一个演示...")
        
        # 5. API服务器演示
        demo_api_server()
        input("\n按回车键继续下一个演示...")
        
        # 6. 安全功能演示
        demo_security_features()
        
        # 新增存储功能演示
        demo_storage_features()
        
        print("\n🎉 所有演示完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n感谢使用高级区块链系统！")


if __name__ == "__main__":
    main() 