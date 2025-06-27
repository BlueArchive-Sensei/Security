"""
加密和签名工具模块
"""
import hashlib
import ecdsa
import base58
import secrets
from typing import Tuple, Optional


class CryptoUtils:
    """加密工具类"""
    
    @staticmethod
    def hash_data(data: str) -> str:
        """使用SHA-256计算数据哈希"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def double_hash(data: str) -> str:
        """双重SHA-256哈希"""
        first_hash = hashlib.sha256(data.encode('utf-8')).digest()
        return hashlib.sha256(first_hash).hexdigest()
    
    @staticmethod
    def generate_private_key() -> str:
        """生成私钥"""
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        return private_key.to_string().hex()
    
    @staticmethod
    def private_key_to_public_key(private_key_hex: str) -> str:
        """从私钥生成公钥"""
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        return public_key.to_string().hex()
    
    @staticmethod
    def public_key_to_address(public_key_hex: str) -> str:
        """从公钥生成地址"""
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # SHA-256哈希
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        
        # RIPEMD-160哈希
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        ripemd160_hash = ripemd160.digest()
        
        # 添加版本字节
        versioned_payload = b'\x00' + ripemd160_hash
        
        # 计算校验和
        checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
        
        # 生成最终地址
        address_bytes = versioned_payload + checksum
        return base58.b58encode(address_bytes).decode()
    
    @staticmethod
    def sign_data(data: str, private_key_hex: str) -> str:
        """对数据进行签名"""
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        
        data_hash = hashlib.sha256(data.encode('utf-8')).digest()
        signature = private_key.sign(data_hash)
        return signature.hex()
    
    @staticmethod
    def verify_signature(data: str, signature_hex: str, public_key_hex: str) -> bool:
        """验证签名"""
        try:
            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = ecdsa.VerifyingKey.from_string(public_key_bytes, curve=ecdsa.SECP256k1)
            
            data_hash = hashlib.sha256(data.encode('utf-8')).digest()
            signature_bytes = bytes.fromhex(signature_hex)
            
            public_key.verify(signature_bytes, data_hash)
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_nonce() -> str:
        """生成随机nonce"""
        return secrets.token_hex(16)


class Wallet:
    """数字钱包类"""
    
    def __init__(self, private_key: Optional[str] = None):
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = CryptoUtils.generate_private_key()
            
        self.public_key = CryptoUtils.private_key_to_public_key(self.private_key)
        self.address = CryptoUtils.public_key_to_address(self.public_key)
    
    def sign_transaction(self, transaction_data: str) -> str:
        """签名交易"""
        return CryptoUtils.sign_data(transaction_data, self.private_key)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'address': self.address
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """从字典创建钱包"""
        return cls(private_key=data['private_key']) 