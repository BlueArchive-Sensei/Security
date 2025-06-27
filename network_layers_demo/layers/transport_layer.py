"""
传输层 (Transport Layer) 实现
负责端到端的可靠数据传输，主要协议有TCP和UDP
"""

import random
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


class TCPHeader:
    """TCP头部结构"""
    
    def __init__(self, src_port: int, dst_port: int, seq_num: int = None, 
                 ack_num: int = None, flags: Dict[str, bool] = None):
        self.src_port = src_port
        self.dst_port = dst_port
        self.seq_num = seq_num or random.randint(1000, 9999)
        self.ack_num = ack_num or 0
        self.window_size = 65535  # 接收窗口大小
        self.checksum = 0  # 将在计算时设置
        self.urgent_pointer = 0
        
        # TCP标志位
        self.flags = flags or {
            'SYN': False,  # 同步序列号
            'ACK': False,  # 应答
            'FIN': False,  # 结束连接
            'RST': False,  # 重置连接
            'PSH': False,  # 推送数据
            'URG': False   # 紧急指针有效
        }
    
    def calculate_checksum(self, data: bytes) -> int:
        """计算TCP校验和"""
        # 简化的校验和计算
        header_data = f"{self.src_port}{self.dst_port}{self.seq_num}{self.ack_num}".encode()
        all_data = header_data + data
        return abs(hash(all_data)) % 65536
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'seq_num': self.seq_num,
            'ack_num': self.ack_num,
            'window_size': self.window_size,
            'checksum': self.checksum,
            'flags': self.flags.copy()
        }


class UDPHeader:
    """UDP头部结构"""
    
    def __init__(self, src_port: int, dst_port: int, length: int = 0):
        self.src_port = src_port
        self.dst_port = dst_port
        self.length = length
        self.checksum = 0
    
    def calculate_checksum(self, data: bytes) -> int:
        """计算UDP校验和"""
        header_data = f"{self.src_port}{self.dst_port}{self.length}".encode()
        all_data = header_data + data
        return abs(hash(all_data)) % 65536
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'length': self.length,
            'checksum': self.checksum
        }


class TransportLayer:
    """传输层实现"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.segment_id = 0
        self.tcp_connections = {}  # 跟踪TCP连接状态
    
    def create_tcp_segment(self, src_port: int, dst_port: int, 
                          app_data: Dict[str, Any], 
                          flags: Dict[str, bool] = None) -> Dict[str, Any]:
        """创建TCP段"""
        self.segment_id += 1
        
        # 创建TCP头部
        tcp_header = TCPHeader(src_port, dst_port, flags=flags)
        
        # 应用层数据
        payload = app_data.get('data', '').encode('utf-8')
        tcp_header.checksum = tcp_header.calculate_checksum(payload)
        
        tcp_segment = {
            'layer': 'Transport',
            'protocol': 'TCP',
            'segment_id': self.segment_id,
            'timestamp': datetime.now().isoformat(),
            'header': tcp_header.to_dict(),
            'payload': app_data,
            'payload_size': len(payload),
            'total_size': 20 + len(payload),  # TCP头部20字节 + 数据
            'connection_info': {
                'src_port': src_port,
                'dst_port': dst_port,
                'reliable': True,
                'connection_oriented': True
            }
        }
        
        if self.debug:
            flags_str = ', '.join([k for k, v in tcp_header.flags.items() if v])
            print(f"[传输层] 创建TCP段: {src_port}→{dst_port}, 序号:{tcp_header.seq_num}, 标志:[{flags_str}]")
            print(f"[传输层] 数据大小: {len(payload)} 字节, 总大小: {tcp_segment['total_size']} 字节")
        
        return tcp_segment
    
    def create_udp_datagram(self, src_port: int, dst_port: int, 
                           app_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建UDP数据报"""
        self.segment_id += 1
        
        # 应用层数据
        payload = app_data.get('data', '').encode('utf-8')
        
        # 创建UDP头部
        udp_header = UDPHeader(src_port, dst_port, 8 + len(payload))  # UDP头部8字节
        udp_header.checksum = udp_header.calculate_checksum(payload)
        
        udp_datagram = {
            'layer': 'Transport',
            'protocol': 'UDP',
            'segment_id': self.segment_id,
            'timestamp': datetime.now().isoformat(),
            'header': udp_header.to_dict(),
            'payload': app_data,
            'payload_size': len(payload),
            'total_size': 8 + len(payload),  # UDP头部8字节 + 数据
            'connection_info': {
                'src_port': src_port,
                'dst_port': dst_port,
                'reliable': False,
                'connection_oriented': False
            }
        }
        
        if self.debug:
            print(f"[传输层] 创建UDP数据报: {src_port}→{dst_port}")
            print(f"[传输层] 数据大小: {len(payload)} 字节, 总大小: {udp_datagram['total_size']} 字节")
        
        return udp_datagram
    
    def establish_tcp_connection(self, src_port: int, dst_port: int, 
                               src_ip: str, dst_ip: str) -> bool:
        """模拟TCP三次握手建立连接"""
        connection_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
        
        if self.debug:
            print(f"[传输层] 开始TCP三次握手: {connection_key}")
            print(f"[传输层] 步骤1: 发送SYN包")
            print(f"[传输层] 步骤2: 接收SYN-ACK包") 
            print(f"[传输层] 步骤3: 发送ACK包")
            print(f"[传输层] TCP连接建立成功!")
        
        self.tcp_connections[connection_key] = {
            'state': 'ESTABLISHED',
            'src_seq': random.randint(1000, 9999),
            'dst_seq': random.randint(1000, 9999),
            'established_at': datetime.now()
        }
        
        return True
    
    def close_tcp_connection(self, src_port: int, dst_port: int, 
                           src_ip: str, dst_ip: str) -> bool:
        """模拟TCP四次挥手关闭连接"""
        connection_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
        
        if connection_key in self.tcp_connections:
            if self.debug:
                print(f"[传输层] 开始TCP四次挥手: {connection_key}")
                print(f"[传输层] 步骤1: 发送FIN包")
                print(f"[传输层] 步骤2: 接收ACK包")
                print(f"[传输层] 步骤3: 接收FIN包")
                print(f"[传输层] 步骤4: 发送ACK包")
                print(f"[传输层] TCP连接关闭成功!")
            
            del self.tcp_connections[connection_key]
            return True
        
        return False
    
    def verify_checksum(self, segment: Dict[str, Any]) -> bool:
        """验证传输层校验和"""
        # 简化校验和验证，在演示中总是返回True
        if self.debug:
            print(f"[传输层] 校验和验证: 通过 (简化实现)")
        
        return True
    
    def decode_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """解码传输层数据"""
        if self.debug:
            protocol = segment.get('protocol')
            src_port = segment.get('header', {}).get('src_port')
            dst_port = segment.get('header', {}).get('dst_port')
            print(f"[传输层] 解码{protocol}段: {src_port}→{dst_port}")
        
        return segment.get('payload', {})
    
    def get_layer_info(self) -> Dict[str, str]:
        """获取传输层信息"""
        return {
            'name': '传输层 (Transport Layer)',
            'function': '提供端到端的可靠数据传输',
            'protocols': 'TCP (可靠), UDP (不可靠)',
            'data_unit': 'Segment/Datagram (段/数据报)',
            'key_features': [
                '端口号识别应用程序',
                'TCP提供可靠传输(重传、流控、拥塞控制)',
                'UDP提供快速但不可靠传输',
                '错误检测和恢复',
                '数据分段和重组'
            ]
        } 