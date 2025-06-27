"""
网络拓扑结构模拟
创建虚拟网络环境，包含多个主机和网络设备
"""

from host import NetworkHost
from typing import Dict, List, Any
import time


class NetworkTopology:
    """网络拓扑结构"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.hosts = {}
        self.switches = {}
        self.routers = {}
        self.connections = []
        
        if self.debug:
            print("[网络拓扑] 网络拓扑初始化完成")
    
    def add_host(self, name: str, ip: str, mac: str = None) -> NetworkHost:
        """添加主机到网络"""
        host = NetworkHost(name, ip, mac, self.debug)
        self.hosts[name] = host
        
        if self.debug:
            print(f"[网络拓扑] 添加主机: {name} ({ip})")
        
        return host
    
    def add_connection(self, host1_name: str, host2_name: str, bandwidth: int = 100):
        """添加主机间的连接"""
        if host1_name in self.hosts and host2_name in self.hosts:
            connection = {
                'host1': host1_name,
                'host2': host2_name,
                'bandwidth': bandwidth,
                'active': True
            }
            self.connections.append(connection)
            
            if self.debug:
                print(f"[网络拓扑] 添加连接: {host1_name} ↔ {host2_name} ({bandwidth} Mbps)")
        else:
            print(f"[网络拓扑] 错误：主机不存在")
    
    def simulate_communication(self, src_host: str, dst_host: str, 
                             message_type: str = "HTTP") -> bool:
        """模拟主机间通信"""
        if src_host not in self.hosts or dst_host not in self.hosts:
            print(f"[网络拓扑] 错误：主机 {src_host} 或 {dst_host} 不存在")
            return False
        
        src = self.hosts[src_host]
        dst = self.hosts[dst_host]
        
        if self.debug:
            print(f"\n{'='*80}")
            print(f"[网络拓扑] 开始模拟通信: {src_host} → {dst_host}")
            print(f"{'='*80}")
        
        # 模拟数据传输
        if message_type == "HTTP":
            # 发送HTTP请求
            transmission = src.send_http_request(dst.ip)
            if transmission:
                time.sleep(0.1)  # 模拟网络延迟
                
                # 接收方处理请求
                received_data = dst.receive_transmission(transmission)
                if received_data:
                    # 发送HTTP响应
                    response = dst.send_http_response(src.ip, 200, "网络分层演示成功！")
                    if response:
                        time.sleep(0.1)  # 模拟网络延迟
                        
                        # 原发送方接收响应
                        final_data = src.receive_transmission(response)
                        
                        if self.debug:
                            print(f"[网络拓扑] 通信成功完成")
                            print(f"{'='*80}\n")
                        
                        return True
        
        if self.debug:
            print(f"[网络拓扑] 通信失败")
            print(f"{'='*80}\n")
        
        return False
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        return {
            'hosts': {name: {
                'ip': host.ip,
                'mac': host.mac
            } for name, host in self.hosts.items()},
            'connections': self.connections,
            'total_hosts': len(self.hosts),
            'total_connections': len(self.connections)
        }
    
    def print_network_summary(self):
        """打印网络摘要"""
        print(f"\n{'='*50}")
        print("网络拓扑摘要")
        print(f"{'='*50}")
        
        print(f"主机总数: {len(self.hosts)}")
        print(f"连接总数: {len(self.connections)}")
        
        print("\n主机列表:")
        for name, host in self.hosts.items():
            print(f"  - {name}: IP={host.ip}, MAC={host.mac}")
        
        print("\n连接列表:")
        for conn in self.connections:
            status = "活跃" if conn['active'] else "断开"
            print(f"  - {conn['host1']} ↔ {conn['host2']} "
                  f"({conn['bandwidth']} Mbps, {status})")
        
        print(f"{'='*50}\n")


def create_demo_network() -> NetworkTopology:
    """创建演示网络拓扑"""
    topology = NetworkTopology(debug=True)
    
    print("\n正在创建演示网络拓扑...")
    
    # 添加主机
    topology.add_host("客户端", "192.168.1.10", "AA:BB:CC:DD:EE:10")
    topology.add_host("服务器", "192.168.1.20", "AA:BB:CC:DD:EE:20")
    topology.add_host("主机A", "192.168.2.10", "BB:CC:DD:EE:FF:10")
    topology.add_host("主机B", "192.168.2.20", "BB:CC:DD:EE:FF:20")
    
    # 添加连接
    topology.add_connection("客户端", "服务器", 100)
    topology.add_connection("客户端", "主机A", 50)
    topology.add_connection("服务器", "主机B", 100)
    topology.add_connection("主机A", "主机B", 10)
    
    topology.print_network_summary()
    
    return topology 