"""
物理层 (Physical Layer) 实现
负责比特流的物理传输，包括电信号、光信号等
"""

import time
import random
from typing import Dict, Any, List
from datetime import datetime


class SignalEncoder:
    """信号编码器"""
    
    @staticmethod
    def encode_nrz(data: bytes) -> List[int]:
        """NRZ (Non-Return-to-Zero) 编码"""
        # 0 → -1, 1 → +1
        bits = []
        for byte in data:
            for i in range(8):
                bit = (byte >> (7 - i)) & 1
                bits.append(1 if bit else -1)
        return bits
    
    @staticmethod
    def encode_manchester(data: bytes) -> List[int]:
        """曼彻斯特编码"""
        # 0 → [-1, +1], 1 → [+1, -1]
        encoded = []
        for byte in data:
            for i in range(8):
                bit = (byte >> (7 - i)) & 1
                if bit:
                    encoded.extend([1, -1])  # 1
                else:
                    encoded.extend([-1, 1])  # 0
        return encoded
    
    @staticmethod
    def decode_signal(signal: List[int], encoding: str) -> bytes:
        """解码信号"""
        if encoding == 'NRZ':
            return SignalEncoder._decode_nrz(signal)
        elif encoding == 'Manchester':
            return SignalEncoder._decode_manchester(signal)
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
    
    @staticmethod
    def _decode_nrz(signal: List[int]) -> bytes:
        """解码NRZ信号"""
        bytes_data = []
        for i in range(0, len(signal), 8):
            byte_bits = signal[i:i+8]
            if len(byte_bits) == 8:
                byte_val = 0
                for j, bit_val in enumerate(byte_bits):
                    if bit_val > 0:
                        byte_val |= (1 << (7 - j))
                bytes_data.append(byte_val)
        return bytes(bytes_data)
    
    @staticmethod
    def _decode_manchester(signal: List[int]) -> bytes:
        """解码曼彻斯特信号"""
        bytes_data = []
        for i in range(0, len(signal), 16):  # 每个字节16个信号点
            byte_signals = signal[i:i+16]
            if len(byte_signals) == 16:
                byte_val = 0
                for j in range(0, 16, 2):
                    # 检查跳变方向
                    if j+1 < len(byte_signals):
                        if byte_signals[j] == 1 and byte_signals[j+1] == -1:
                            # +1, -1 表示 1
                            byte_val |= (1 << (7 - j//2))
                        # -1, +1 表示 0 (不需要设置位)
                bytes_data.append(byte_val)
        return bytes(bytes_data)


class TransmissionMedium:
    """传输介质"""
    
    def __init__(self, medium_type: str = "copper", bandwidth: int = 100):
        self.medium_type = medium_type  # copper, fiber, wireless
        self.bandwidth = bandwidth      # Mbps
        self.latency = self._calculate_latency()
        self.error_rate = self._calculate_error_rate()
    
    def _calculate_latency(self) -> float:
        """计算传输延迟"""
        latency_map = {
            'copper': 0.0001,    # 0.1ms
            'fiber': 0.00005,    # 0.05ms
            'wireless': 0.0005   # 0.5ms
        }
        return latency_map.get(self.medium_type, 0.0001)
    
    def _calculate_error_rate(self) -> float:
        """计算误码率"""
        error_rate_map = {
            'copper': 1e-9,      # 10^-9
            'fiber': 1e-12,      # 10^-12
            'wireless': 1e-6     # 10^-6
        }
        return error_rate_map.get(self.medium_type, 1e-9)
    
    def transmit(self, signal: List[int]) -> List[int]:
        """在介质中传输信号"""
        # 模拟传输延迟
        time.sleep(self.latency)
        
        # 模拟信号噪声和错误
        transmitted_signal = signal.copy()
        for i in range(len(transmitted_signal)):
            if random.random() < self.error_rate:
                # 翻转信号
                transmitted_signal[i] = -transmitted_signal[i]
        
        return transmitted_signal


class PhysicalLayer:
    """物理层实现"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.transmission_id = 0
        self.encoder = SignalEncoder()
        self.medium = TransmissionMedium()
    
    def set_transmission_medium(self, medium_type: str, bandwidth: int = 100):
        """设置传输介质"""
        self.medium = TransmissionMedium(medium_type, bandwidth)
        if self.debug:
            print(f"[物理层] 设置传输介质: {medium_type}, 带宽: {bandwidth} Mbps")
    
    def transmit_frame(self, frame: Dict[str, Any], encoding: str = "NRZ") -> Dict[str, Any]:
        """传输帧数据"""
        self.transmission_id += 1
        
        # 将帧数据转换为字节
        frame_data = str(frame).encode('utf-8')
        
        if self.debug:
            print(f"[物理层] 开始传输: 帧ID {frame.get('frame_id')}")
            print(f"[物理层] 数据大小: {len(frame_data)} 字节")
            print(f"[物理层] 编码方式: {encoding}")
            print(f"[物理层] 传输介质: {self.medium.medium_type}")
        
        # 编码数据为信号
        if encoding == "NRZ":
            signal = self.encoder.encode_nrz(frame_data)
        elif encoding == "Manchester":
            signal = self.encoder.encode_manchester(frame_data)
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
        
        if self.debug:
            print(f"[物理层] 信号长度: {len(signal)} 个符号")
            print(f"[物理层] 开始物理传输...")
        
        # 在传输介质中传输
        start_time = time.time()
        transmitted_signal = self.medium.transmit(signal)
        transmission_time = time.time() - start_time
        
        # 计算传输速率
        data_bits = len(frame_data) * 8
        if transmission_time > 0:
            actual_rate = data_bits / transmission_time / 1_000_000  # Mbps
        else:
            actual_rate = self.medium.bandwidth
        
        transmission_info = {
            'layer': 'Physical',
            'transmission_id': self.transmission_id,
            'timestamp': datetime.now().isoformat(),
            'frame': frame,
            'signal_encoding': encoding,
            'signal_length': len(signal),
            'transmission_medium': {
                'type': self.medium.medium_type,
                'bandwidth': self.medium.bandwidth,
                'latency': self.medium.latency,
                'error_rate': self.medium.error_rate
            },
            'transmission_stats': {
                'data_size': len(frame_data),
                'signal_size': len(signal),
                'transmission_time': transmission_time,
                'actual_rate_mbps': actual_rate,
                'signal_errors': sum(1 for i in range(len(signal)) if signal[i] != transmitted_signal[i])
            },
            'received_signal': transmitted_signal
        }
        
        if self.debug:
            print(f"[物理层] 传输完成，用时: {transmission_time:.4f}s")
            print(f"[物理层] 实际传输速率: {actual_rate:.2f} Mbps")
            print(f"[物理层] 信号错误: {transmission_info['transmission_stats']['signal_errors']} 个")
        
        return transmission_info
    
    def receive_transmission(self, transmission_info: Dict[str, Any]) -> Dict[str, Any]:
        """接收传输的数据"""
        if self.debug:
            print(f"[物理层] 接收传输: ID {transmission_info.get('transmission_id')}")
        
        # 从传输信息中提取信号
        received_signal = transmission_info.get('received_signal', [])
        encoding = transmission_info.get('signal_encoding', 'NRZ')
        
        if self.debug:
            print(f"[物理层] 解码信号: {encoding} 编码")
        
        try:
            # 解码信号回帧数据
            decoded_data = self.encoder.decode_signal(received_signal, encoding)
            
            # 尝试恢复帧结构（简化处理）
            frame_str = decoded_data.decode('utf-8', errors='ignore')
            
            if self.debug:
                print(f"[物理层] 信号解码成功")
                print(f"[物理层] 恢复数据大小: {len(decoded_data)} 字节")
            
            return transmission_info.get('frame', {})
            
        except Exception as e:
            if self.debug:
                print(f"[物理层] 信号解码失败: {str(e)}")
            return {}
    
    def detect_carrier(self) -> bool:
        """载波检测 (Carrier Sense)"""
        # 模拟载波检测
        carrier_present = random.random() < 0.1  # 10%概率检测到载波
        
        if self.debug and carrier_present:
            print(f"[物理层] 检测到载波信号，等待空闲...")
        
        return carrier_present
    
    def measure_signal_quality(self, signal: List[int]) -> Dict[str, float]:
        """测量信号质量"""
        if not signal:
            return {'snr': 0.0, 'power': 0.0, 'quality': 0.0}
        
        # 计算信号功率（简化）
        power = sum(x*x for x in signal) / len(signal)
        
        # 模拟信噪比
        snr = random.uniform(20, 40)  # 20-40 dB
        
        # 计算整体质量评分
        quality = min(100, max(0, (snr - 10) * 5))  # 0-100分
        
        quality_info = {
            'snr_db': snr,
            'power': power,
            'quality_score': quality
        }
        
        if self.debug:
            print(f"[物理层] 信号质量: SNR={snr:.1f}dB, 功率={power:.2f}, 质量={quality:.1f}/100")
        
        return quality_info
    
    def get_layer_info(self) -> Dict[str, str]:
        """获取物理层信息"""
        return {
            'name': '物理层 (Physical Layer)',
            'function': '负责比特流的物理传输',
            'protocols': '以太网物理层, WiFi物理层, 光纤等',
            'data_unit': 'Bit (比特)',
            'key_features': [
                '电信号/光信号/无线信号传输',
                '信号编码和调制(NRZ, 曼彻斯特等)',
                '传输介质特性(铜缆, 光纤, 无线)',
                '载波检测和冲突检测',
                '信号放大和中继',
                '物理连接和拓扑结构'
            ]
        } 