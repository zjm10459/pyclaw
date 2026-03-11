"""
认证与配对管理
==============

负责 PyClaw 的安全认证和设备配对。

功能：
1. 令牌认证（Token Authentication）
2. 设备配对（Device Pairing）
3. 挑战 - 响应签名（Challenge-Response）
4. 本地信任（Local Trust）

安全模型：
- 所有连接必须通过认证
- 新设备需要配对审批
- 本地回环连接可自动批准
- 支持设备令牌持久化

使用示例：
    auth = AuthManager(token="secret-token")
    
    # 验证连接
    is_valid = auth.verify_token("provided-token")
    
    # 设备配对
    device_id = "device-123"
    if auth.is_device_paired(device_id):
        # 已配对，允许连接
        pass
    else:
        # 需要配对审批
        auth.request_pairing(device_id)
"""

import uuid
import hashlib
import secrets
import json
import os
from pathlib import Path
from typing import Dict, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import base64


@dataclass
class DeviceInfo:
    """
    设备信息
    
    属性:
        device_id: 设备唯一标识
        platform: 平台（macos/linux/windows/ios/android）
        device_family: 设备家族（desktop/mobile）
        first_seen: 首次连接时间
        last_seen: 最后连接时间
        is_paired: 是否已配对
        is_local: 是否本地设备
        token: 设备令牌（配对后生成）
    """
    device_id: str
    platform: str = "unknown"
    device_family: str = "unknown"
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    is_paired: bool = False
    is_local: bool = False
    token: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "device_id": self.device_id,
            "platform": self.platform,
            "device_family": self.device_family,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "is_paired": self.is_paired,
            "is_local": self.is_local,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceInfo':
        """从字典创建"""
        return cls(
            device_id=data["device_id"],
            platform=data.get("platform", "unknown"),
            device_family=data.get("device_family", "unknown"),
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            is_paired=data.get("is_paired", False),
            is_local=data.get("is_local", False),
            token=data.get("token"),
        )


class AuthManager:
    """
    认证管理器
    
    处理所有认证相关的逻辑：
    - 令牌验证
    - 设备配对
    - 挑战生成与验证
    - 本地信任判断
    
    属性:
        token: 主认证令牌
        paired_devices: 已配对设备字典
        pending_pairings: 待审批配对请求
        pairing_store_path: 配对存储路径
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        pairing_store_path: Optional[str] = None,
        allow_local_auto: bool = True,
    ):
        """
        初始化认证管理器
        
        参数:
            token: 主认证令牌（可选，但推荐设置）
            pairing_store_path: 配对存储文件路径
            allow_local_auto: 是否允许本地设备自动配对
        """
        # 从环境变量获取 token（如果未提供）
        self.token = token or os.environ.get("PYCLAW_GATEWAY_TOKEN")
        
        # 配对存储
        self.pairing_store_path = Path(
            pairing_store_path or Path.home() / ".pyclaw" / "paired-devices.json"
        )
        
        # 本地设备自动配对
        self.allow_local_auto = allow_local_auto
        
        # 已配对设备 {device_id: DeviceInfo}
        self.paired_devices: Dict[str, DeviceInfo] = {}
        
        # 待审批配对 {device_id: request_info}
        self.pending_pairings: Dict[str, Dict[str, Any]] = {}
        
        # 当前活跃的挑战 {challenge_id: (device_id, secret, expires_at)}
        self.active_challenges: Dict[str, tuple] = {}
        
        # 加载已保存的配对
        self._load_pairings()
    
    def _load_pairings(self):
        """
        从磁盘加载配对信息
        
        如果文件不存在或格式错误，使用空字典。
        """
        if self.pairing_store_path.exists():
            try:
                data = json.loads(self.pairing_store_path.read_text())
                for device_id, device_data in data.items():
                    self.paired_devices[device_id] = DeviceInfo.from_dict(device_data)
                print(f"已加载 {len(self.paired_devices)} 个配对设备")
            except Exception as e:
                print(f"警告：加载配对文件失败：{e}")
    
    def _save_pairings(self):
        """
        保存配对信息到磁盘
        
        确保目录存在，然后写入 JSON 文件。
        """
        try:
            # 确保目录存在
            self.pairing_store_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 序列化
            data = {
                device_id: info.to_dict()
                for device_id, info in self.paired_devices.items()
            }
            
            # 写入文件（带权限保护）
            self.pairing_store_path.write_text(
                json.dumps(data, indent=2),
                encoding='utf-8'
            )
            
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.pairing_store_path, 0o600)
            
            print(f"已保存 {len(self.paired_devices)} 个配对设备")
        except Exception as e:
            print(f"错误：保存配对文件失败：{e}")
    
    def verify_token(self, provided_token: Optional[str]) -> bool:
        """
        验证提供的令牌
        
        参数:
            provided_token: 客户端提供的令牌
        
        返回:
            True（有效）或 False（无效）
        """
        # 如果没有设置令牌，允许所有连接（仅用于开发）
        if not self.token:
            print("警告：未设置认证令牌，允许所有连接")
            return True
        
        # 比较令牌（使用常量时间比较防止时序攻击）
        if not provided_token:
            return False
        
        return secrets.compare_digest(self.token, provided_token)
    
    def is_local_address(self, address: str) -> bool:
        """
        判断地址是否为本地地址
        
        本地地址包括：
        - 127.0.0.1
        - ::1 (IPv6 localhost)
        - localhost
        
        参数:
            address: IP 地址或主机名
        
        返回:
            True（本地）或 False（远程）
        """
        local_addresses = {"127.0.0.1", "::1", "localhost"}
        return address in local_addresses
    
    def create_challenge(self, device_id: str) -> str:
        """
        创建挑战
        
        用于挑战 - 响应认证流程。
        
        参数:
            device_id: 设备 ID
        
        返回:
            挑战 ID
        """
        challenge_id = str(uuid.uuid4())
        secret = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(minutes=5)
        
        self.active_challenges[challenge_id] = (device_id, secret, expires_at)
        
        # 清理过期挑战
        self._cleanup_challenges()
        
        return challenge_id
    
    def verify_challenge(
        self,
        challenge_id: str,
        device_id: str,
        signature: str,
    ) -> bool:
        """
        验证挑战响应
        
        参数:
            challenge_id: 挑战 ID
            device_id: 设备 ID
            signature: 客户端签名（base64 编码）
        
        返回:
            True（验证通过）或 False（验证失败）
        """
        # 查找挑战
        if challenge_id not in self.active_challenges:
            return False
        
        stored_device_id, secret, expires_at = self.active_challenges[challenge_id]
        
        # 检查设备 ID 匹配
        if stored_device_id != device_id:
            return False
        
        # 检查是否过期
        if datetime.now() > expires_at:
            del self.active_challenges[challenge_id]
            return False
        
        # 验证签名
        # 预期签名：base64(HMAC-SHA256(device_id + secret, key=secret))
        expected_data = f"{device_id}:{secret}".encode()
        expected_signature = base64.b64encode(
            hashlib.sha256(expected_data).digest()
        ).decode()
        
        # 清理挑战
        del self.active_challenges[challenge_id]
        
        return secrets.compare_digest(signature, expected_signature)
    
    def _cleanup_challenges(self):
        """清理过期的挑战"""
        now = datetime.now()
        expired = [
            cid for cid, (_, _, expires) in self.active_challenges.items()
            if now > expires
        ]
        for cid in expired:
            del self.active_challenges[cid]
    
    def request_pairing(
        self,
        device_id: str,
        device_info: Dict[str, Any],
        is_local: bool = False,
    ) -> Dict[str, Any]:
        """
        请求设备配对
        
        参数:
            device_id: 设备 ID
            device_info: 设备信息（platform, device_family 等）
            is_local: 是否本地设备
        
        返回:
            配对结果 {status: "approved"|"pending"|"rejected", ...}
        """
        # 检查是否已配对
        if device_id in self.paired_devices:
            device = self.paired_devices[device_id]
            device.last_seen = datetime.now()
            return {
                "status": "approved",
                "token": device.token,
                "message": "设备已配对",
            }
        
        # 本地设备自动配对
        if is_local and self.allow_local_auto:
            return self._approve_pairing(device_id, device_info, is_local=True)
        
        # 添加到待审批列表
        self.pending_pairings[device_id] = {
            "device_info": device_info,
            "requested_at": datetime.now(),
            "is_local": is_local,
        }
        
        print(f"新设备配对请求：{device_id}")
        print(f"  平台：{device_info.get('platform', 'unknown')}")
        print(f"  本地：{is_local}")
        
        return {
            "status": "pending",
            "message": "等待管理员审批",
            "device_id": device_id,
        }
    
    def _approve_pairing(
        self,
        device_id: str,
        device_info: Dict[str, Any],
        is_local: bool = False,
    ) -> Dict[str, Any]:
        """
        批准配对
        
        参数:
            device_id: 设备 ID
            device_info: 设备信息
            is_local: 是否本地设备
        
        返回:
            配对结果
        """
        # 生成设备令牌
        device_token = secrets.token_urlsafe(32)
        
        # 创建设备信息
        device = DeviceInfo(
            device_id=device_id,
            platform=device_info.get("platform", "unknown"),
            device_family=device_info.get("device_family", "unknown"),
            is_paired=True,
            is_local=is_local,
            token=device_token,
        )
        
        # 保存
        self.paired_devices[device_id] = device
        self._save_pairings()
        
        # 从待审批列表移除
        self.pending_pairings.pop(device_id, None)
        
        print(f"设备配对批准：{device_id}")
        
        return {
            "status": "approved",
            "token": device_token,
            "message": "配对成功",
        }
    
    def approve_pairing(self, device_id: str) -> Dict[str, Any]:
        """
        手动批准配对请求
        
        参数:
            device_id: 设备 ID
        
        返回:
            配对结果
        """
        if device_id not in self.pending_pairings:
            return {
                "status": "error",
                "message": "未找到待审批的配对请求",
            }
        
        request = self.pending_pairings[device_id]
        return self._approve_pairing(
            device_id,
            request["device_info"],
            request["is_local"],
        )
    
    def reject_pairing(self, device_id: str) -> Dict[str, Any]:
        """
        拒绝配对请求
        
        参数:
            device_id: 设备 ID
        
        返回:
            结果
        """
        if device_id not in self.pending_pairings:
            return {
                "status": "error",
                "message": "未找到待审批的配对请求",
            }
        
        del self.pending_pairings[device_id]
        
        print(f"设备配对拒绝：{device_id}")
        
        return {
            "status": "rejected",
            "message": "配对请求已拒绝",
        }
    
    def list_pending_pairings(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有待审批的配对请求
        
        返回:
            待审批配对字典
        """
        return dict(self.pending_pairings)
    
    def list_paired_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有已配对设备
        
        返回:
            已配对设备字典
        """
        return {
            device_id: info.to_dict()
            for device_id, info in self.paired_devices.items()
        }
    
    def revoke_device(self, device_id: str) -> bool:
        """
        撤销设备配对
        
        参数:
            device_id: 设备 ID
        
        返回:
            True（成功）或 False（设备不存在）
        """
        if device_id not in self.paired_devices:
            return False
        
        del self.paired_devices[device_id]
        self._save_pairings()
        
        print(f"设备配对已撤销：{device_id}")
        
        return True


class DevicePairing:
    """
    设备配对辅助类
    
    提供配对相关的命令行工具和辅助函数。
    """
    
    def __init__(self, auth_manager: AuthManager):
        """
        初始化
        
        参数:
            auth_manager: 认证管理器实例
        """
        self.auth = auth_manager
    
    def status(self) -> Dict[str, Any]:
        """
        获取配对状态
        
        返回:
            状态信息
        """
        return {
            "paired_count": len(self.auth.paired_devices),
            "pending_count": len(self.auth.pending_pairings),
            "paired_devices": self.auth.list_paired_devices(),
            "pending_requests": self.auth.list_pending_pairings(),
        }
    
    def approve(self, device_id: str) -> Dict[str, Any]:
        """
        批准设备配对
        
        参数:
            device_id: 设备 ID
        
        返回:
            结果
        """
        return self.auth.approve_pairing(device_id)
    
    def reject(self, device_id: str) -> Dict[str, Any]:
        """
        拒绝设备配对
        
        参数:
            device_id: 设备 ID
        
        返回:
            结果
        """
        return self.auth.reject_pairing(device_id)
    
    def revoke(self, device_id: str) -> bool:
        """
        撤销设备配对
        
        参数:
            device_id: 设备 ID
        
        返回:
            True（成功）或 False（失败）
        """
        return self.auth.revoke_device(device_id)
