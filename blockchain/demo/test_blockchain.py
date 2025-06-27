#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
区块链功能测试脚本

用于验证区块链的核心功能是否正常工作
"""

import sys
import os
from blockchain import Blockchain, Block, Transaction, SimpleWallet

def test_block_creation():
    """测试区块创建功能"""
    print("测试区块创建...")
    
    # 创建一个测试区块
    block = Block(1, "测试数据", "0000")
    
    # 验证区块属性
    assert block.index == 1
    assert block.data == "测试数据"
    assert block.previous_hash == "0000"
    assert block.nonce == 0
    assert len(block.hash) == 64  # SHA-256哈希长度
    
    print("✅ 区块创建测试通过")

def test_blockchain_creation():
    """测试区块链创建功能"""
    print("测试区块链创建...")
    
    # 创建区块链
    blockchain = Blockchain()
    
    # 验证创世区块
    assert len(blockchain.chain) == 1
    assert blockchain.chain[0].index == 0
    assert blockchain.chain[0].previous_hash == "0"
    assert blockchain.is_chain_valid()
    
    print("✅ 区块链创建测试通过")

def test_block_addition():
    """测试区块添加功能"""
    print("测试区块添加...")
    
    # 创建区块链并添加区块
    blockchain = Blockchain()
    blockchain.difficulty = 1  # 降低难度以加快测试
    
    # 添加几个区块
    blockchain.create_and_add_block("第一个区块")
    blockchain.create_and_add_block("第二个区块")
    blockchain.create_and_add_block("第三个区块")
    
    # 验证区块链
    assert len(blockchain.chain) == 4  # 包括创世区块
    assert blockchain.is_chain_valid()
    
    # 验证区块链接
    for i in range(1, len(blockchain.chain)):
        current_block = blockchain.chain[i]
        previous_block = blockchain.chain[i-1]
        assert current_block.previous_hash == previous_block.hash
    
    print("✅ 区块添加测试通过")

def test_chain_validation():
    """测试区块链验证功能"""
    print("测试区块链验证...")
    
    # 创建区块链
    blockchain = Blockchain()
    blockchain.difficulty = 1
    blockchain.create_and_add_block("测试区块")
    
    # 验证正常的链
    assert blockchain.is_chain_valid()
    
    # 测试篡改检测
    original_data = blockchain.chain[1].data
    blockchain.chain[1].data = "被篡改的数据"
    assert not blockchain.is_chain_valid()
    
    # 恢复数据
    blockchain.chain[1].data = original_data
    blockchain.chain[1].hash = blockchain.chain[1].calculate_hash()
    assert blockchain.is_chain_valid()
    
    print("✅ 区块链验证测试通过")

def test_transaction_system():
    """测试交易系统功能"""
    print("测试交易系统...")
    
    # 创建钱包
    alice = SimpleWallet("Alice", 100)
    bob = SimpleWallet("Bob", 50)
    
    # 验证初始余额
    assert alice.get_balance() == 100
    assert bob.get_balance() == 50
    
    # 执行交易
    tx = alice.send_money("Bob", 30)
    assert tx is not None
    assert alice.get_balance() == 70
    
    bob.receive_money("Alice", 30)
    assert bob.get_balance() == 80
    
    # 测试余额不足的情况
    tx_fail = alice.send_money("Bob", 200)
    assert tx_fail is None
    assert alice.get_balance() == 70  # 余额不应该改变
    
    print("✅ 交易系统测试通过")

def test_mining_proof_of_work():
    """测试挖矿工作量证明"""
    print("测试挖矿工作量证明...")
    
    # 创建区块并设置较低难度
    block = Block(1, "测试挖矿", "0000")
    difficulty = 2
    
    # 挖矿
    block.mine_block(difficulty)
    
    # 验证挖矿结果
    assert block.hash.startswith("0" * difficulty)
    assert block.nonce > 0
    
    print("✅ 挖矿工作量证明测试通过")

def test_data_serialization():
    """测试数据序列化功能"""
    print("测试数据序列化...")
    
    # 创建区块链
    blockchain = Blockchain()
    blockchain.difficulty = 1
    blockchain.create_and_add_block("序列化测试")
    
    # 获取区块链信息
    info = blockchain.get_blockchain_info()
    
    # 验证序列化数据
    assert 'total_blocks' in info
    assert 'difficulty' in info
    assert 'is_valid' in info
    assert 'chain' in info
    assert info['total_blocks'] == 2
    
    print("✅ 数据序列化测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行区块链功能测试")
    print("=" * 50)
    
    tests = [
        test_block_creation,
        test_blockchain_creation,
        test_block_addition,
        test_chain_validation,
        test_transaction_system,
        test_mining_proof_of_work,
        test_data_serialization
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 测试失败: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 所有测试都通过了！区块链功能正常。")
        return True
    else:
        print("⚠️  有一些测试失败，请检查代码。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 