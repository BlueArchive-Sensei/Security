"""
应用层 (Application Layer) 实现
负责为应用程序提供网络服务，如HTTP、FTP、SMTP等协议
"""

import json
from typing import Dict, Any
from datetime import datetime


class HTTPMessage:
    """HTTP消息类，模拟HTTP协议"""
    
    def __init__(self, method: str = "GET", url: str = "/", 
                 headers: Dict[str, str] = None, body: str = ""):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.timestamp = datetime.now()
        
        # 设置默认头部
        if 'Host' not in self.headers:
            self.headers['Host'] = 'localhost'
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = 'NetworkDemo/1.0'
        if 'Content-Length' not in self.headers and body:
            self.headers['Content-Length'] = str(len(body))
    
    def to_string(self) -> str:
        """将HTTP消息转换为字符串格式"""
        lines = [f"{self.method} {self.url} HTTP/1.1"]
        
        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")  # 空行分隔头部和主体
        if self.body:
            lines.append(self.body)
            
        return "\r\n".join(lines)
    
    def get_size(self) -> int:
        """获取HTTP消息的大小（字节）"""
        return len(self.to_string().encode('utf-8'))


class HTTPResponse:
    """HTTP响应类"""
    
    def __init__(self, status_code: int = 200, status_text: str = "OK",
                 headers: Dict[str, str] = None, body: str = ""):
        self.status_code = status_code
        self.status_text = status_text
        self.headers = headers or {}
        self.body = body
        self.timestamp = datetime.now()
        
        # 设置默认头部
        if 'Server' not in self.headers:
            self.headers['Server'] = 'NetworkDemo/1.0'
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'text/html'
        if 'Content-Length' not in self.headers and body:
            self.headers['Content-Length'] = str(len(body))
    
    def to_string(self) -> str:
        """将HTTP响应转换为字符串格式"""
        lines = [f"HTTP/1.1 {self.status_code} {self.status_text}"]
        
        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")  # 空行分隔头部和主体
        if self.body:
            lines.append(self.body)
            
        return "\r\n".join(lines)
    
    def get_size(self) -> int:
        """获取HTTP响应的大小（字节）"""
        return len(self.to_string().encode('utf-8'))


class ApplicationLayer:
    """应用层实现"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.message_id = 0
    
    def create_http_request(self, method: str, url: str, 
                          headers: Dict[str, str] = None, body: str = "") -> HTTPMessage:
        """创建HTTP请求"""
        if self.debug:
            print(f"[应用层] 创建HTTP请求: {method} {url}")
        
        return HTTPMessage(method, url, headers, body)
    
    def create_http_response(self, status_code: int = 200, 
                           body: str = "") -> HTTPResponse:
        """创建HTTP响应"""
        if self.debug:
            print(f"[应用层] 创建HTTP响应: {status_code}")
        
        return HTTPResponse(status_code, body=body)
    
    def process_request(self, http_message: HTTPMessage) -> Dict[str, Any]:
        """处理HTTP请求，返回应用层数据包"""
        self.message_id += 1
        
        app_data = {
            'layer': 'Application',
            'protocol': 'HTTP',
            'message_id': self.message_id,
            'timestamp': datetime.now().isoformat(),
            'data': http_message.to_string(),
            'size': http_message.get_size(),
            'headers': {
                'method': http_message.method,
                'url': http_message.url,
                'http_headers': http_message.headers
            }
        }
        
        if self.debug:
            print(f"[应用层] 处理请求完成，数据大小: {app_data['size']} 字节")
            print(f"[应用层] HTTP报文: {http_message.method} {http_message.url}")
        
        return app_data
    
    def process_response(self, http_response: HTTPResponse) -> Dict[str, Any]:
        """处理HTTP响应，返回应用层数据包"""
        self.message_id += 1
        
        app_data = {
            'layer': 'Application',
            'protocol': 'HTTP',
            'message_id': self.message_id,
            'timestamp': datetime.now().isoformat(),
            'data': http_response.to_string(),
            'size': http_response.get_size(),
            'headers': {
                'status_code': http_response.status_code,
                'status_text': http_response.status_text,
                'http_headers': http_response.headers
            }
        }
        
        if self.debug:
            print(f"[应用层] 处理响应完成，状态码: {http_response.status_code}")
            print(f"[应用层] 响应数据大小: {app_data['size']} 字节")
        
        return app_data
    
    def decode_data(self, app_data: Dict[str, Any]) -> str:
        """解码应用层数据"""
        if self.debug:
            protocol = app_data.get('protocol', 'Unknown')
            size = app_data.get('size', 0)
            print(f"[应用层] 解码 {protocol} 数据，大小: {size} 字节")
        
        return app_data.get('data', '')
    
    def get_layer_info(self) -> Dict[str, str]:
        """获取应用层信息"""
        return {
            'name': '应用层 (Application Layer)',
            'function': '为应用程序提供网络服务',
            'protocols': 'HTTP, HTTPS, FTP, SMTP, DNS, SSH等',
            'data_unit': 'Message (消息)',
            'key_features': [
                '直接与用户应用程序交互',
                '提供各种网络服务协议',
                '数据格式化和编码',
                '用户界面和API接口'
            ]
        } 