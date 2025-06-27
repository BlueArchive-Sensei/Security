#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
区块链Demo演示脚本

这个脚本展示了区块链的各种功能：
1. 创建区块链
2. 添加区块
3. 挖矿过程
4. 区块链验证
5. 交易模拟
6. 数据持久化

运行此脚本可以看到完整的区块链运行过程
"""

import time
import json
from blockchain import Blockchain, Block, Transaction, SimpleWallet

def print_separator(title=""):
    """打印分隔符"""
    print("\n" + "=" * 80)
    if title:
        print(f"{title:^80}")
        print("=" * 80)

def demo_basic_blockchain():
    """演示基本的区块链功能"""
    print_separator("基本区块链演示")
    
    # 创建新的区块链
    print("🚀 创建新的区块链...")
    my_blockchain = Blockchain()
    
    # 添加一些区块
    print("\n📦 添加新区块到区块链...")
    
    # 第一个区块 - 用户注册信息
    my_blockchain.create_and_add_block("用户张三注册了系统")
    
    # 第二个区块 - 交易信息
    my_blockchain.create_and_add_block("张三向李四转账50元")
    
    # 第三个区块 - 更多交易
    my_blockchain.create_and_add_block("李四向王五转账30元")
    
    # 显示整个区块链
    print("\n📋 显示完整的区块链信息:")
    my_blockchain.print_blockchain()
    
    # 验证区块链
    print(f"\n✅ 区块链验证结果: {'有效' if my_blockchain.is_chain_valid() else '无效'}")
    
    return my_blockchain

def demo_blockchain_tampering(blockchain):
    """演示区块链防篡改功能"""
    print_separator("区块链防篡改演示")
    
    print("🔒 尝试篡改区块链数据...")
    
    # 尝试修改第二个区块的数据
    print("修改第2个区块的数据...")
    blockchain.chain[2].data = "张三向李四转账100元（被篡改！）"
    
    # 验证区块链（应该无效）
    print(f"篡改后的验证结果: {'有效' if blockchain.is_chain_valid() else '无效'}")
    
    # 恢复原始数据
    print("\n🔧 恢复区块链数据...")
    blockchain.chain[2].data = "张三向李四转账50元"
    blockchain.chain[2].hash = blockchain.chain[2].calculate_hash()
    
    print(f"恢复后的验证结果: {'有效' if blockchain.is_chain_valid() else '无效'}")

def demo_transaction_system():
    """演示交易系统"""
    print_separator("交易系统演示")
    
    # 创建钱包
    print("💳 创建用户钱包...")
    alice = SimpleWallet("Alice", 100)
    bob = SimpleWallet("Bob", 50)
    charlie = SimpleWallet("Charlie", 75)
    
    print(f"Alice 初始余额: {alice.get_balance()}")
    print(f"Bob 初始余额: {bob.get_balance()}")
    print(f"Charlie 初始余额: {charlie.get_balance()}")
    
    # 创建区块链用于记录交易
    transaction_blockchain = Blockchain()
    
    # 执行一系列交易
    print("\n💸 执行交易...")
    
    # Alice 向 Bob 转账
    tx1 = alice.send_money("Bob", 25)
    if tx1:
        bob.receive_money("Alice", 25)
        transaction_blockchain.create_and_add_block(f"交易: {tx1.to_string()}")
    
    # Bob 向 Charlie 转账
    tx2 = bob.send_money("Charlie", 30)
    if tx2:
        charlie.receive_money("Bob", 30)
        transaction_blockchain.create_and_add_block(f"交易: {tx2.to_string()}")
    
    # Charlie 向 Alice 转账
    tx3 = charlie.send_money("Alice", 40)
    if tx3:
        alice.receive_money("Charlie", 40)
        transaction_blockchain.create_and_add_block(f"交易: {tx3.to_string()}")
    
    # 显示最终余额
    print("\n💰 交易后的余额:")
    print(f"Alice: {alice.get_balance()}")
    print(f"Bob: {bob.get_balance()}")
    print(f"Charlie: {charlie.get_balance()}")
    
    # 显示交易区块链
    print("\n📊 交易区块链:")
    transaction_blockchain.print_blockchain()
    
    return transaction_blockchain

def demo_mining_difficulty():
    """演示不同挖矿难度的效果"""
    print_separator("挖矿难度演示")
    
    print("⛏️  测试不同挖矿难度的性能...")
    
    for difficulty in [1, 2, 3, 4]:
        print(f"\n测试难度级别: {difficulty}")
        
        # 创建测试区块链
        test_blockchain = Blockchain()
        test_blockchain.difficulty = difficulty
        
        # 记录时间
        start_time = time.time()
        
        # 添加一个测试区块
        test_blockchain.create_and_add_block(f"难度{difficulty}的测试区块")
        
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        print(f"难度{difficulty}的总挖矿时间: {total_time}秒")

def demo_persistence(blockchain):
    """演示数据持久化功能"""
    print_separator("数据持久化演示")
    
    # 保存区块链到文件
    filename = "my_blockchain.json"
    print(f"💾 保存区块链到文件: {filename}")
    blockchain.save_to_file(filename)
    
    # 读取并显示保存的数据
    print(f"\n📖 读取保存的区块链数据:")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print(f"保存的区块总数: {saved_data['total_blocks']}")
        print(f"保存的挖矿难度: {saved_data['difficulty']}")
        print(f"保存时的链状态: {'有效' if saved_data['is_valid'] else '无效'}")
        print(f"最新区块哈希: {saved_data['latest_block_hash']}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")

def interactive_demo():
    """交互式演示"""
    print_separator("交互式区块链演示")
    
    blockchain = Blockchain()
    print("🎮 欢迎使用交互式区块链演示！")
    print("你可以添加自定义数据到区块链中")
    
    while True:
        print("\n选择操作:")
        print("1. 添加新区块")
        print("2. 查看区块链")
        print("3. 验证区块链")
        print("4. 保存区块链")
        print("5. 退出")
        
        try:
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == '1':
                data = input("请输入区块数据: ").strip()
                if data:
                    blockchain.create_and_add_block(data)
                else:
                    print("数据不能为空！")
            
            elif choice == '2':
                blockchain.print_blockchain()
            
            elif choice == '3':
                result = blockchain.is_chain_valid()
                print(f"区块链验证结果: {'有效' if result else '无效'}")
            
            elif choice == '4':
                filename = input("请输入文件名 (默认: interactive_blockchain.json): ").strip()
                if not filename:
                    filename = "interactive_blockchain.json"
                blockchain.save_to_file(filename)
            
            elif choice == '5':
                print("感谢使用区块链演示！")
                break
            
            else:
                print("无效选择，请重新输入！")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")

def main():
    """主函数 - 运行所有演示"""
    print("🌟 欢迎使用区块链Demo！")
    print("这个演示将展示区块链的各种功能和特性")
    
    try:
        # 1. 基本区块链演示
        blockchain = demo_basic_blockchain()
        
        # 等待用户按键继续
        input("\n按回车键继续下一个演示...")
        
        # 2. 防篡改演示
        demo_blockchain_tampering(blockchain)
        
        input("\n按回车键继续下一个演示...")
        
        # 3. 交易系统演示
        transaction_blockchain = demo_transaction_system()
        
        input("\n按回车键继续下一个演示...")
        
        # 4. 挖矿难度演示
        demo_mining_difficulty()
        
        input("\n按回车键继续下一个演示...")
        
        # 5. 数据持久化演示
        demo_persistence(transaction_blockchain)
        
        # 6. 询问是否运行交互式演示
        print("\n" + "=" * 80)
        choice = input("是否运行交互式演示？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            interactive_demo()
        
        print_separator("演示完成")
        print("🎉 所有演示已完成！")
        print("📚 查看生成的JSON文件了解区块链数据结构")
        print("🔍 你可以修改代码来实验不同的功能")
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 