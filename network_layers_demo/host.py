"""
虚拟主机实现
模拟网络中的主机节点，包含完整的网络协议栈
"""

from layers import *
from typing import Dict, Any, Optional, List
import random


class NetworkHost:
    """网络主机类"""
    
    def __init__(self, name: str, ip: str, mac: str = None, debug: bool = True):
        self.name = name
        self.ip = ip
        self.mac = mac or self._generate_mac()
        self.debug = debug
        
        # 初始化各层
        self.application_layer = ApplicationLayer(debug)
        self.transport_layer = TransportLayer(debug)
        self.network_layer = NetworkLayer(debug)
        self.datalink_layer = DataLinkLayer(debug)
        self.physical_layer = PhysicalLayer(debug)
        
        if self.debug:
            print(f"[主机 {self.name}] 初始化完成: IP={self.ip}, MAC={self.mac}")
    
    def _generate_mac(self) -> str:
        """生成随机MAC地址"""
        mac_parts = []
        for _ in range(6):
            mac_parts.append(f"{random.randint(0, 255):02X}")
        return ":".join(mac_parts)
    
    def send_http_request(self, dst_ip: str, method: str = "GET", 
                         url: str = "/", port: int = 80) -> Dict[str, Any]:
        """发送HTTP请求"""
        if self.debug:
            print(f"\n{'='*60}")
            print(f"[主机 {self.name}] 开始发送HTTP请求到 {dst_ip}")
            print(f"{'='*60}")
        
        # 1. 应用层：创建HTTP请求
        http_request = self.application_layer.create_http_request(method, url)
        app_data = self.application_layer.process_request(http_request)
        
        # 2. 传输层：创建TCP段
        tcp_segment = self.transport_layer.create_tcp_segment(
            src_port=random.randint(1024, 65535),
            dst_port=port,
            app_data=app_data
        )
        
        # 3. 网络层：创建IP数据包
        ip_packet = self.network_layer.create_ip_packet(
            src_ip=self.ip,
            dst_ip=dst_ip,
            transport_data=tcp_segment
        )
        
        # 4. 数据链路层：创建以太网帧
        ethernet_frame = self.datalink_layer.create_ethernet_frame(
            src_mac=self.mac,
            dst_ip=dst_ip,
            network_data=ip_packet
        )
        
        if not ethernet_frame:
            print(f"[主机 {self.name}] 发送失败：无法创建以太网帧")
            return {}
        
        # 5. 物理层：传输帧
        transmission = self.physical_layer.transmit_frame(ethernet_frame)
        
        if self.debug:
            print(f"[主机 {self.name}] HTTP请求发送完成")
            print(f"{'='*60}\n")
        
        return transmission
    
    def receive_transmission(self, transmission: Dict[str, Any]) -> Optional[str]:
        """接收并处理传输的数据"""
        if self.debug:
            print(f"\n{'='*60}")
            print(f"[主机 {self.name}] 开始接收数据")
            print(f"{'='*60}")
        
        # 1. 物理层：接收信号
        ethernet_frame = self.physical_layer.receive_transmission(transmission)
        if not ethernet_frame:
            print(f"[主机 {self.name}] 物理层接收失败")
            return None
        
        # 2. 数据链路层：解码帧
        if not self.datalink_layer.verify_frame_integrity(ethernet_frame):
            print(f"[主机 {self.name}] 帧校验失败，丢弃帧")
            return None
        
        ip_packet = self.datalink_layer.decode_frame(ethernet_frame)
        
        # 3. 网络层：解码数据包
        if not self.network_layer.verify_checksum(ip_packet):
            print(f"[主机 {self.name}] IP校验失败，丢弃数据包")
            return None
        
        tcp_segment = self.network_layer.decode_packet(ip_packet)
        
        # 4. 传输层：解码段
        if not self.transport_layer.verify_checksum(tcp_segment):
            print(f"[主机 {self.name}] TCP校验失败，丢弃段")
            return None
        
        app_data = self.transport_layer.decode_segment(tcp_segment)
        
        # 5. 应用层：解码数据
        http_data = self.application_layer.decode_data(app_data)
        
        if self.debug:
            print(f"[主机 {self.name}] 数据接收完成")
            print(f"{'='*60}\n")
        
        return http_data
    
    def send_http_response(self, dst_ip: str, status_code: int = 200, 
                          body: str = "Hello World!", port: int = 80) -> Dict[str, Any]:
        """发送HTTP响应"""
        if self.debug:
            print(f"\n{'='*60}")
            print(f"[主机 {self.name}] 开始发送HTTP响应到 {dst_ip}")
            print(f"{'='*60}")
        
        # 1. 应用层：创建HTTP响应
        http_response = self.application_layer.create_http_response(status_code, body)
        app_data = self.application_layer.process_response(http_response)
        
        # 2. 传输层：创建TCP段
        tcp_segment = self.transport_layer.create_tcp_segment(
            src_port=port,
            dst_port=random.randint(1024, 65535),
            app_data=app_data
        )
        
        # 3. 网络层：创建IP数据包
        ip_packet = self.network_layer.create_ip_packet(
            src_ip=self.ip,
            dst_ip=dst_ip,
            transport_data=tcp_segment
        )
        
        # 4. 数据链路层：创建以太网帧
        ethernet_frame = self.datalink_layer.create_ethernet_frame(
            src_mac=self.mac,
            dst_ip=dst_ip,
            network_data=ip_packet
        )
        
        if not ethernet_frame:
            print(f"[主机 {self.name}] 发送失败：无法创建以太网帧")
            return {}
        
        # 5. 物理层：传输帧
        transmission = self.physical_layer.transmit_frame(ethernet_frame)
        
        if self.debug:
            print(f"[主机 {self.name}] HTTP响应发送完成")
            print(f"{'='*60}\n")
        
        return transmission
    
    def ping(self, dst_ip: str) -> bool:
        """发送PING请求（简化版）"""
        if self.debug:
            print(f"[主机 {self.name}] PING {dst_ip}")
        
        # 简化实现，直接检查路由
        route = self.network_layer.routing_table.find_route(dst_ip)
        success = route is not None
        
        if self.debug:
            status = "成功" if success else "失败"
            print(f"[主机 {self.name}] PING {dst_ip}: {status}")
        
        return success
    
    def traceroute(self, dst_ip: str) -> List[str]:
        """跟踪路由（简化版）"""
        if self.debug:
            print(f"[主机 {self.name}] 跟踪到 {dst_ip} 的路由")
        
        hops = []
        route = self.network_layer.routing_table.find_route(dst_ip)
        
        if route:
            hops.append(self.ip)
            if route['gateway'] != dst_ip:
                hops.append(route['gateway'])
            hops.append(dst_ip)
        
        if self.debug:
            for i, hop in enumerate(hops, 1):
                print(f"[主机 {self.name}] {i}. {hop}")
        
        return hops
    
    def get_network_stack_info(self) -> Dict[str, Dict[str, Any]]:
        """获取网络协议栈信息"""
        return {
            'host_info': {
                'name': self.name,
                'ip': self.ip,
                'mac': self.mac
            },
            'layers': {
                'application': self.application_layer.get_layer_info(),
                'transport': self.transport_layer.get_layer_info(),
                'network': self.network_layer.get_layer_info(),
                'datalink': self.datalink_layer.get_layer_info(),
                'physical': self.physical_layer.get_layer_info()
            },
            'tables': {
                'routing_table': self.network_layer.get_routing_table(),
                'arp_table': self.datalink_layer.get_arp_table()
            }
        } 