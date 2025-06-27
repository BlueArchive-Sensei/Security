#!/usr/bin/env python3
"""
计算机网络分层通信演示程序
展示TCP/IP五层模型的完整数据传输过程
"""

import time
import sys
from colorama import init, Fore, Style
from tabulate import tabulate
from network_topology import create_demo_network, NetworkTopology
from host import NetworkHost


def print_header():
    """打印程序标题"""
    init()  # 初始化colorama
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print("🌐 计算机网络分层通信演示程序")
    print("📚 TCP/IP五层模型数据传输过程可视化")
    print(f"{'='*80}{Style.RESET_ALL}\n")


def print_layer_info(host: NetworkHost):
    """打印网络分层信息"""
    stack_info = host.get_network_stack_info()
    
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}网络协议栈层次结构:{Style.RESET_ALL}")
    
    layer_data = []
    for layer_name, layer_info in stack_info['layers'].items():
        layer_data.append([
            layer_info['name'],
            layer_info['function'],
            layer_info['data_unit'],
            ', '.join(layer_info['protocols'])
        ])
    
    headers = ['层次', '功能', '数据单位', '主要协议']
    print(tabulate(layer_data, headers=headers, tablefmt='grid'))


def print_routing_table(host: NetworkHost):
    """打印路由表"""
    stack_info = host.get_network_stack_info()
    routing_table = stack_info['tables']['routing_table']
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}路由表:{Style.RESET_ALL}")
    
    route_data = []
    for route in routing_table:
        route_data.append([
            route['network'],
            route['netmask'],
            route['gateway'],
            route['interface'],
            route['metric']
        ])
    
    headers = ['目标网络', '子网掩码', '网关', '接口', '跃点数']
    print(tabulate(route_data, headers=headers, tablefmt='grid'))


def print_arp_table(host: NetworkHost):
    """打印ARP表"""
    stack_info = host.get_network_stack_info()
    arp_table = stack_info['tables']['arp_table']
    
    print(f"\n{Fore.BLUE}{Style.BRIGHT}ARP表:{Style.RESET_ALL}")
    
    arp_data = []
    for ip, entry in arp_table.items():
        arp_data.append([
            ip,
            entry['mac'],
            '静态' if entry['static'] else '动态',
            entry['timestamp'].strftime('%H:%M:%S')
        ])
    
    headers = ['IP地址', 'MAC地址', '类型', '时间']
    print(tabulate(arp_data, headers=headers, tablefmt='grid'))


def demo_scenario_1(topology: NetworkTopology):
    """演示场景1：基本HTTP通信"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")
    print("📡 演示场景1: HTTP请求响应通信")
    print("🔄 客户端 → 服务器 (同一网段)")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    success = topology.simulate_communication("客户端", "服务器", "HTTP")
    
    if success:
        print(f"{Fore.GREEN}✅ 场景1演示成功完成！{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ 场景1演示失败！{Style.RESET_ALL}")
    
    return success


def demo_scenario_2(topology: NetworkTopology):
    """演示场景2：跨网段通信"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")
    print("📡 演示场景2: 跨网段通信")
    print("🌐 主机A → 主机B (不同网段)")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    success = topology.simulate_communication("主机A", "主机B", "HTTP")
    
    if success:
        print(f"{Fore.GREEN}✅ 场景2演示成功完成！{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ 场景2演示失败！{Style.RESET_ALL}")
    
    return success


def demo_network_tools(topology: NetworkTopology):
    """演示网络工具"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")
    print("🔧 演示场景3: 网络诊断工具")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    client = topology.hosts["客户端"]
    
    # PING测试
    print(f"\n{Fore.CYAN}PING测试:{Style.RESET_ALL}")
    targets = ["192.168.1.20", "192.168.2.10", "192.168.2.20"]
    
    for target in targets:
        result = client.ping(target)
        status = f"{Fore.GREEN}✅ 成功{Style.RESET_ALL}" if result else f"{Fore.RED}❌ 失败{Style.RESET_ALL}"
        print(f"  PING {target}: {status}")
    
    # Traceroute测试
    print(f"\n{Fore.CYAN}路由跟踪:{Style.RESET_ALL}")
    hops = client.traceroute("192.168.2.20")
    for i, hop in enumerate(hops, 1):
        print(f"  {i}. {hop}")


def interactive_mode(topology: NetworkTopology):
    """交互模式"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}进入交互模式...{Style.RESET_ALL}")
    print("可用命令:")
    print("  1 - 运行场景1 (基本HTTP通信)")
    print("  2 - 运行场景2 (跨网段通信)")
    print("  3 - 网络诊断工具")
    print("  info - 显示网络信息")
    print("  layers - 显示协议栈信息")
    print("  routes - 显示路由表")
    print("  arp - 显示ARP表")
    print("  quit - 退出程序")
    
    while True:
        try:
            command = input(f"\n{Fore.CYAN}网络演示> {Style.RESET_ALL}").strip().lower()
            
            if command == '1':
                demo_scenario_1(topology)
            elif command == '2':
                demo_scenario_2(topology)
            elif command == '3':
                demo_network_tools(topology)
            elif command == 'info':
                topology.print_network_summary()
            elif command == 'layers':
                print_layer_info(topology.hosts["客户端"])
            elif command == 'routes':
                print_routing_table(topology.hosts["客户端"])
            elif command == 'arp':
                print_arp_table(topology.hosts["客户端"])
            elif command == 'quit':
                print(f"{Fore.YELLOW}👋 感谢使用网络分层演示程序！{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}未知命令: {command}{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 程序被用户中断{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")


def main():
    """主函数"""
    print_header()
    
    # 创建网络拓扑
    topology = create_demo_network()
    
    # 显示协议栈信息
    print_layer_info(topology.hosts["客户端"])
    
    # 运行演示场景
    print(f"\n{Fore.CYAN}{Style.BRIGHT}开始运行演示场景...{Style.RESET_ALL}")
    
    # 场景1：基本通信
    demo_scenario_1(topology)
    time.sleep(2)
    
    # 场景2：跨网段通信
    demo_scenario_2(topology)
    time.sleep(2)
    
    # 场景3：网络工具
    demo_network_tools(topology)
    
    # 显示网络表
    print_routing_table(topology.hosts["客户端"])
    print_arp_table(topology.hosts["客户端"])
    
    # 询问是否进入交互模式
    print(f"\n{Fore.YELLOW}演示完成！是否进入交互模式？ (y/n): {Style.RESET_ALL}", end="")
    
    try:
        choice = input().strip().lower()
        if choice in ['y', 'yes', 'Y', '是']:
            interactive_mode(topology)
        else:
            print(f"{Fore.GREEN}感谢使用网络分层演示程序！{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 程序结束{Style.RESET_ALL}")


if __name__ == "__main__":
    main() 