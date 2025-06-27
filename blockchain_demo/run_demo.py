#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
区块链Demo启动脚本

用户可以选择运行测试或演示
"""

import sys
import subprocess

def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("🌟 欢迎使用区块链Demo！")
    print("=" * 60)
    print("这是一个功能完整的区块链演示项目")
    print("包含区块创建、挖矿、交易、验证等核心功能")
    print("=" * 60)

def run_tests():
    """运行测试"""
    print("\n🧪 开始运行功能测试...")
    try:
        result = subprocess.run([sys.executable, "test_blockchain.py"], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def run_demo():
    """运行演示"""
    print("\n🎮 开始运行区块链演示...")
    try:
        subprocess.run([sys.executable, "demo.py"], capture_output=False, text=True)
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"运行演示时出错: {e}")

def main():
    """主函数"""
    print_welcome()
    
    while True:
        print("\n请选择要执行的操作:")
        print("1. 🧪 运行功能测试 (验证区块链功能是否正常)")
        print("2. 🎮 运行完整演示 (体验区块链各种功能)")
        print("3. 🔧 先测试后演示 (推荐)")
        print("4. 📚 显示帮助信息")
        print("5. 🚪 退出")
        
        try:
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == '1':
                success = run_tests()
                if success:
                    print("\n✅ 所有测试通过！区块链功能正常。")
                else:
                    print("\n❌ 测试失败，请检查代码。")
            
            elif choice == '2':
                run_demo()
            
            elif choice == '3':
                print("\n📋 执行推荐流程：先运行测试，再运行演示")
                success = run_tests()
                if success:
                    print("\n✅ 测试通过！现在开始演示...")
                    input("按回车键开始演示...")
                    run_demo()
                else:
                    print("\n❌ 测试失败，建议修复问题后再运行演示。")
            
            elif choice == '4':
                show_help()
            
            elif choice == '5':
                print("\n👋 感谢使用区块链Demo！")
                break
            
            else:
                print("\n❌ 无效选择，请输入1-5的数字。")
        
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {e}")

def show_help():
    """显示帮助信息"""
    print("\n" + "=" * 60)
    print("📚 区块链Demo帮助信息")
    print("=" * 60)
    print("🔧 项目结构:")
    print("  ├── blockchain.py       # 区块链核心实现")
    print("  ├── demo.py            # 演示脚本")
    print("  ├── test_blockchain.py # 功能测试脚本")
    print("  ├── run_demo.py        # 启动脚本（本文件）")
    print("  └── README.md         # 详细说明文档")
    print()
    print("🎯 功能说明:")
    print("  • 功能测试: 验证区块链各项功能是否正常工作")
    print("  • 完整演示: 展示区块链的创建、挖矿、交易等功能")
    print("  • 交互式体验: 可以手动添加区块和数据")
    print()
    print("📖 详细文档:")
    print("  查看 README.md 文件获取完整的使用说明")
    print("=" * 60)

if __name__ == "__main__":
    main() 