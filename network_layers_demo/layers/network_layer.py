"""
网络层 (Network Layer) 实现
负责数据包的路由和转发，主要协议是IP
"""

import random
import struct
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class IPHeader:
    """IP头部结构"""
    
    def __init__(self, src_ip: str, dst_ip: str, protocol: int = 6):  # 6=TCP, 17=UDP
        self.version = 4  # IPv4
        self.header_length = 5  # 20字节 (5 * 4)
        self.type_of_service = 0
        self.total_length = 0  # 将在设置数据时计算
        self.identification = random.randint(1, 65535)
        self.flags = 0  # 不分片
        self.fragment_offset = 0
        self.ttl = 64  # 生存时间
        self.protocol = protocol
        self.header_checksum = 0  # 将在计算时设置
        self.src_ip = src_ip
        self.dst_ip = dst_ip
    
    def calculate_checksum(self) -> int:
        """计算IP头部校验和"""
        # 简化的校验和计算
        header_data = f"{self.version}{self.header_length}{self.total_length}{self.identification}{self.ttl}{self.protocol}{self.src_ip}{self.dst_ip}"
        return abs(hash(header_data)) % 65536
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'version': self.version,
            'header_length': self.header_length,
            'type_of_service': self.type_of_service,
            'total_length': self.total_length,
            'identification': self.identification,
            'flags': self.flags,
            'fragment_offset': self.fragment_offset,
            'ttl': self.ttl,
            'protocol': self.protocol,
            'header_checksum': self.header_checksum,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip
        }


class RoutingTable:
    """路由表"""
    
    def __init__(self):
        self.routes = []
    
    def add_route(self, network: str, netmask: str, gateway: str, interface: str):
        """添加路由条目"""
        self.routes.append({
            'network': network,
            'netmask': netmask,
            'gateway': gateway,
            'interface': interface,
            'metric': 1
        })
    
    def find_route(self, dst_ip: str) -> Optional[Dict[str, str]]:
        """查找路由"""
        # 简化的路由查找逻辑
        for route in self.routes:
            if self._ip_in_network(dst_ip, route['network'], route['netmask']):
                return route
        
        # 返回默认路由
        for route in self.routes:
            if route['network'] == '0.0.0.0':
                return route
        
        return None
    
    def _ip_in_network(self, ip: str, network: str, netmask: str) -> bool:
        """判断IP是否在指定网络中"""
        # 简化实现：只检查前三个八位组
        ip_parts = ip.split('.')
        net_parts = network.split('.')
        
        if network == '0.0.0.0':  # 默认路由
            return True
        
        # 检查前三个八位组是否匹配 (假设/24网络)
        return (ip_parts[0] == net_parts[0] and 
                ip_parts[1] == net_parts[1] and 
                ip_parts[2] == net_parts[2])


class NetworkLayer:
    """网络层实现"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.packet_id = 0
        self.routing_table = RoutingTable()
        self._init_routing_table()
    
    def _init_routing_table(self):
        """初始化路由表"""
        # 添加一些示例路由
        self.routing_table.add_route('192.168.1.0', '255.255.255.0', '192.168.1.1', 'eth0')
        self.routing_table.add_route('192.168.2.0', '255.255.255.0', '192.168.1.1', 'eth0')
        self.routing_table.add_route('10.0.0.0', '255.0.0.0', '192.168.1.1', 'eth0')
        self.routing_table.add_route('0.0.0.0', '0.0.0.0', '192.168.1.1', 'eth0')  # 默认路由
    
    def create_ip_packet(self, src_ip: str, dst_ip: str, 
                        transport_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建IP数据包"""
        self.packet_id += 1
        
        # 确定协议类型
        protocol_map = {'TCP': 6, 'UDP': 17}
        protocol = protocol_map.get(transport_data.get('protocol', 'TCP'), 6)
        
        # 创建IP头部
        ip_header = IPHeader(src_ip, dst_ip, protocol)
        
        # 计算总长度 (IP头部 + 传输层数据)
        payload_size = transport_data.get('total_size', 0)
        ip_header.total_length = 20 + payload_size  # IP头部20字节
        ip_header.header_checksum = ip_header.calculate_checksum()
        
        # 查找路由
        route = self.routing_table.find_route(dst_ip)
        next_hop = route['gateway'] if route else dst_ip
        
        ip_packet = {
            'layer': 'Network',
            'protocol': 'IP',
            'packet_id': self.packet_id,
            'timestamp': datetime.now().isoformat(),
            'header': ip_header.to_dict(),
            'payload': transport_data,
            'payload_size': payload_size,
            'total_size': ip_header.total_length,
            'routing_info': {
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'next_hop': next_hop,
                'route': route,
                'ttl': ip_header.ttl
            }
        }
        
        if self.debug:
            print(f"[网络层] 创建IP数据包: {src_ip} → {dst_ip}")
            print(f"[网络层] 数据包ID: {self.packet_id}, TTL: {ip_header.ttl}")
            print(f"[网络层] 下一跳: {next_hop}, 总大小: {ip_header.total_length} 字节")
            if route:
                print(f"[网络层] 路由: {route['network']} via {route['gateway']} dev {route['interface']}")
        
        return ip_packet
    
    def route_packet(self, packet: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """路由数据包"""
        header = packet.get('header', {})
        dst_ip = header.get('dst_ip')
        ttl = header.get('ttl', 0)
        
        if ttl <= 0:
            if self.debug:
                print(f"[网络层] 数据包TTL超时，丢弃数据包")
            return False, "TTL expired"
        
        # TTL减1
        header['ttl'] = ttl - 1
        
        # 查找路由
        route = self.routing_table.find_route(dst_ip)
        if not route:
            if self.debug:
                print(f"[网络层] 没有找到到达 {dst_ip} 的路由")
            return False, "No route to host"
        
        next_hop = route['gateway']
        
        if self.debug:
            print(f"[网络层] 路由数据包到 {dst_ip}, 下一跳: {next_hop}")
            print(f"[网络层] TTL剩余: {header['ttl']}")
        
        return True, next_hop
    
    def fragment_packet(self, packet: Dict[str, Any], mtu: int = 1500) -> List[Dict[str, Any]]:
        """分片IP数据包"""
        total_size = packet.get('total_size', 0)
        
        if total_size <= mtu:
            if self.debug:
                print(f"[网络层] 数据包大小 {total_size} <= MTU {mtu}, 无需分片")
            return [packet]
        
        if self.debug:
            print(f"[网络层] 数据包大小 {total_size} > MTU {mtu}, 开始分片")
        
        fragments = []
        header = packet['header'].copy()
        payload = packet['payload']
        
        # 计算每个分片的数据大小 (减去IP头部20字节)
        fragment_data_size = mtu - 20
        fragment_data_size = (fragment_data_size // 8) * 8  # 必须是8的倍数
        
        payload_data = str(payload).encode('utf-8')
        offset = 0
        fragment_id = 0
        
        while offset < len(payload_data):
            fragment_id += 1
            end_offset = min(offset + fragment_data_size, len(payload_data))
            is_last_fragment = (end_offset == len(payload_data))
            
            # 创建分片头部
            frag_header = header.copy()
            frag_header['identification'] = header['identification']
            frag_header['fragment_offset'] = offset // 8
            frag_header['flags'] = 0 if is_last_fragment else 1  # MF位
            frag_header['total_length'] = 20 + (end_offset - offset)
            
            # 创建分片
            fragment = {
                'layer': 'Network',
                'protocol': 'IP',
                'packet_id': f"{packet['packet_id']}.{fragment_id}",
                'timestamp': datetime.now().isoformat(),
                'header': frag_header,
                'payload': payload_data[offset:end_offset].decode('utf-8', errors='ignore'),
                'total_size': frag_header['total_length'],
                'fragment_info': {
                    'is_fragment': True,
                    'fragment_id': fragment_id,
                    'offset': offset,
                    'is_last': is_last_fragment
                }
            }
            
            fragments.append(fragment)
            offset = end_offset
            
            if self.debug:
                print(f"[网络层] 创建分片 {fragment_id}: 偏移={offset//8}, 大小={frag_header['total_length']}, 最后分片={is_last_fragment}")
        
        return fragments
    
    def verify_checksum(self, packet: Dict[str, Any]) -> bool:
        """验证IP头部校验和"""
        # 简化校验和验证，在演示中总是返回True
        if self.debug:
            print(f"[网络层] IP头部校验和验证: 通过 (简化实现)")
        
        return True
    
    def decode_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """解码网络层数据包"""
        if self.debug:
            header = packet.get('header', {})
            src_ip = header.get('src_ip')
            dst_ip = header.get('dst_ip')
            protocol = header.get('protocol')
            protocol_name = {6: 'TCP', 17: 'UDP'}.get(protocol, str(protocol))
            print(f"[网络层] 解码IP数据包: {src_ip} → {dst_ip}, 协议: {protocol_name}")
        
        return packet.get('payload', {})
    
    def get_routing_table(self) -> List[Dict[str, str]]:
        """获取路由表"""
        return self.routing_table.routes
    
    def get_layer_info(self) -> Dict[str, str]:
        """获取网络层信息"""
        return {
            'name': '网络层 (Network Layer)',
            'function': '负责数据包的路由和转发',
            'protocols': 'IP, ICMP, ARP, OSPF, BGP等',
            'data_unit': 'Packet (数据包)',
            'key_features': [
                'IP地址标识网络中的主机',
                '路由选择和数据包转发',
                '数据包分片和重组',
                '生存时间(TTL)控制',
                '网络互连和跨网段通信'
            ]
        } 