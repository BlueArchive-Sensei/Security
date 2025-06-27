"""
数据链路层 (Data Link Layer) 实现
负责同一网段内的数据传输，主要协议是以太网
"""

import random
from typing import Dict, Any, Optional
from datetime import datetime


class EthernetHeader:
    """以太网帧头部结构"""
    
    def __init__(self, src_mac: str, dst_mac: str, ether_type: int = 0x0800):  # 0x0800 = IPv4
        self.dst_mac = dst_mac  # 目标MAC地址
        self.src_mac = src_mac  # 源MAC地址
        self.ether_type = ether_type  # 以太网类型
        self.frame_check_sequence = 0  # 帧校验序列，将在计算时设置
    
    def calculate_fcs(self, data: bytes) -> int:
        """计算帧校验序列(FCS)"""
        # 简化的CRC32计算
        header_data = f"{self.dst_mac}{self.src_mac}{self.ether_type}".encode()
        all_data = header_data + data
        return abs(hash(all_data)) % (2**32)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'dst_mac': self.dst_mac,
            'src_mac': self.src_mac,
            'ether_type': hex(self.ether_type),
            'frame_check_sequence': self.frame_check_sequence
        }


class ARPTable:
    """ARP表 - IP地址到MAC地址的映射"""
    
    def __init__(self):
        self.table = {}
    
    def add_entry(self, ip: str, mac: str):
        """添加ARP条目"""
        self.table[ip] = {
            'mac': mac,
            'timestamp': datetime.now(),
            'static': False
        }
    
    def lookup(self, ip: str) -> Optional[str]:
        """查找MAC地址"""
        entry = self.table.get(ip)
        return entry['mac'] if entry else None
    
    def get_table(self) -> Dict[str, Dict[str, Any]]:
        """获取完整ARP表"""
        return self.table.copy()


class DataLinkLayer:
    """数据链路层实现"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.frame_id = 0
        self.arp_table = ARPTable()
        self._init_arp_table()
    
    def _init_arp_table(self):
        """初始化ARP表"""
        # 添加一些示例ARP条目
        self.arp_table.add_entry('192.168.1.1', '00:11:22:33:44:55')   # 网关
        self.arp_table.add_entry('192.168.1.10', 'AA:BB:CC:DD:EE:10')  # 主机1
        self.arp_table.add_entry('192.168.1.20', 'AA:BB:CC:DD:EE:20')  # 主机2
        self.arp_table.add_entry('192.168.2.10', 'BB:CC:DD:EE:FF:10')  # 主机3
        self.arp_table.add_entry('192.168.2.20', 'BB:CC:DD:EE:FF:20')  # 主机4
    
    def resolve_mac_address(self, ip: str) -> Optional[str]:
        """解析IP地址对应的MAC地址（模拟ARP协议）"""
        mac = self.arp_table.lookup(ip)
        
        if mac:
            if self.debug:
                print(f"[数据链路层] ARP解析: {ip} → {mac} (从缓存)")
        else:
            # 模拟ARP请求过程
            if self.debug:
                print(f"[数据链路层] 发送ARP请求: Who has {ip}?")
                print(f"[数据链路层] 等待ARP响应...")
            
            # 生成随机MAC地址作为响应（模拟）
            mac = self._generate_mac_address()
            self.arp_table.add_entry(ip, mac)
            
            if self.debug:
                print(f"[数据链路层] ARP响应: {ip} is at {mac}")
        
        return mac
    
    def _generate_mac_address(self) -> str:
        """生成随机MAC地址"""
        mac_parts = []
        for _ in range(6):
            mac_parts.append(f"{random.randint(0, 255):02X}")
        return ":".join(mac_parts)
    
    def create_ethernet_frame(self, src_mac: str, dst_ip: str, 
                             network_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建以太网帧"""
        self.frame_id += 1
        
        # 解析目标MAC地址
        dst_mac = self.resolve_mac_address(dst_ip)
        if not dst_mac:
            if self.debug:
                print(f"[数据链路层] 无法解析目标IP {dst_ip} 的MAC地址")
            return None
        
        # 创建以太网头部
        eth_header = EthernetHeader(src_mac, dst_mac)
        
        # 网络层数据作为载荷
        payload_data = str(network_data).encode('utf-8')
        eth_header.frame_check_sequence = eth_header.calculate_fcs(payload_data)
        
        ethernet_frame = {
            'layer': 'DataLink',
            'protocol': 'Ethernet',
            'frame_id': self.frame_id,
            'timestamp': datetime.now().isoformat(),
            'header': eth_header.to_dict(),
            'payload': network_data,
            'payload_size': len(payload_data),
            'total_size': 14 + len(payload_data) + 4,  # 头部14字节 + 数据 + FCS4字节
            'addressing': {
                'src_mac': src_mac,
                'dst_mac': dst_mac,
                'dst_ip': dst_ip,
                'broadcast': (dst_mac == 'FF:FF:FF:FF:FF:FF')
            }
        }
        
        if self.debug:
            print(f"[数据链路层] 创建以太网帧: {src_mac} → {dst_mac}")
            print(f"[数据链路层] 帧ID: {self.frame_id}, 大小: {ethernet_frame['total_size']} 字节")
            print(f"[数据链路层] 以太网类型: {eth_header.to_dict()['ether_type']}")
        
        return ethernet_frame
    
    def verify_frame_integrity(self, frame: Dict[str, Any]) -> bool:
        """验证帧完整性（FCS校验）"""
        # 简化帧校验，在演示中总是返回True
        if self.debug:
            print(f"[数据链路层] 帧校验序列(FCS)验证: 通过 (简化实现)")
        
        return True
    
    def detect_collision(self) -> bool:
        """检测冲突（CSMA/CD）"""
        # 模拟冲突检测
        collision_probability = 0.05  # 5%的冲突概率
        has_collision = random.random() < collision_probability
        
        if has_collision and self.debug:
            print(f"[数据链路层] 检测到冲突！启动退避算法...")
            print(f"[数据链路层] 随机退避后重新发送...")
        
        return has_collision
    
    def switch_learning(self, frame: Dict[str, Any], port: int):
        """交换机学习MAC地址"""
        src_mac = frame.get('header', {}).get('src_mac')
        if src_mac and self.debug:
            print(f"[数据链路层] 交换机学习: MAC {src_mac} 在端口 {port}")
    
    def forward_frame(self, frame: Dict[str, Any]) -> bool:
        """转发帧"""
        dst_mac = frame.get('header', {}).get('dst_mac')
        
        # 检查目标MAC地址
        if dst_mac == 'FF:FF:FF:FF:FF:FF':
            # 广播帧
            if self.debug:
                print(f"[数据链路层] 广播帧，向所有端口转发")
            return True
        else:
            # 单播帧
            if self.debug:
                print(f"[数据链路层] 单播帧，转发到 {dst_mac}")
            return True
    
    def decode_frame(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """解码数据链路层帧"""
        if self.debug:
            header = frame.get('header', {})
            src_mac = header.get('src_mac')
            dst_mac = header.get('dst_mac')
            ether_type = header.get('ether_type')
            print(f"[数据链路层] 解码以太网帧: {src_mac} → {dst_mac}, 类型: {ether_type}")
        
        return frame.get('payload', {})
    
    def get_arp_table(self) -> Dict[str, Dict[str, Any]]:
        """获取ARP表"""
        return self.arp_table.get_table()
    
    def get_layer_info(self) -> Dict[str, str]:
        """获取数据链路层信息"""
        return {
            'name': '数据链路层 (Data Link Layer)',
            'function': '负责同一网段内的可靠数据传输',
            'protocols': 'Ethernet, Wi-Fi, PPP, ARP等',
            'data_unit': 'Frame (帧)',
            'key_features': [
                'MAC地址物理寻址',
                '帧同步和界定',
                '错误检测和纠正(FCS)',
                '流量控制',
                'CSMA/CD冲突检测',
                'ARP协议地址解析'
            ]
        } 