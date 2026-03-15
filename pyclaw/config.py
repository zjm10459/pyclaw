#!/usr/bin/env python3
"""
Pyclaw 配置管理器 - 统一的配置加载和缓存中心
=====================================

功能：
- 单例模式，全局共享配置实例
- 自动缓存，避免重复加载
- 支持多模块配置隔离
- 配置变更自动通知（可选）
- 配置持久化到 JSON 文件

使用示例：
    from pyclaw.config import ConfigManager
    
    # 获取单例实例
    config = ConfigManager.get_instance()
    
    # 获取配置
    app_config = config.get("app")
    db_host = config.get("app", "db_host", "localhost")
    
    # 设置配置
    config.set("app", "debug", True)
    
    # 保存配置到文件
    config.save()
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime


# 配置根目录 - pyclaw 项目配置目录
CONFIG_ROOT = Path(__file__).parent.parent / "config"
CONFIG_ROOT.mkdir(parents=True, exist_ok=True)

# 兼容旧配置路径
LEGACY_CONFIG_PATHS = [
    Path.home() / ".pyclaw" / "config.json",
    Path.home() / ".pyclaw" / "config.json5",
    Path(__file__).parent.parent / "config.json",
]


class ConfigManager:
    """
    配置管理器 - 单例模式
    
    特性：
    - 线程安全
    - 自动缓存
    - 懒加载
    - 支持配置变更回调
    - 兼容旧配置路径
    """
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ConfigManager':
        """单例模式 - 确保只有一个实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._file_paths: Dict[str, Path] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._last_modified: Dict[str, datetime] = {}
        self._migrated_legacy = False
        
        # 自动加载所有现有配置
        self._auto_load_all()
        
        # 迁移旧配置（如果需要）
        self._migrate_legacy_config()
    
    def _auto_load_all(self):
        """自动加载所有现有的配置文件"""
        if not CONFIG_ROOT.exists():
            return
        
        for config_file in CONFIG_ROOT.glob("*.json"):
            module_name = config_file.stem
            if module_name.startswith("_"):
                continue
            try:
                self._load_file(module_name, config_file)
            except Exception as e:
                print(f"⚠️  加载配置失败 {module_name}: {e}")
    
    def _load_file(self, module_name: str, file_path: Path) -> Dict[str, Any]:
        """从文件加载配置"""
        if not file_path.exists():
            return {}
        
        content = file_path.read_text(encoding="utf-8")
        config = json.loads(content)
        
        self._cache[module_name] = config
        self._file_paths[module_name] = file_path
        self._last_modified[module_name] = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        return config
    
    def _migrate_legacy_config(self):
        """迁移旧配置到新系统"""
        if self._migrated_legacy:
            return
        
        for legacy_path in LEGACY_CONFIG_PATHS:
            if legacy_path.exists():
                try:
                    legacy_config = json.loads(legacy_path.read_text(encoding="utf-8"))
                    
                    # 合并到主配置
                    if legacy_config:
                        # 将旧配置保存为 main 模块
                        if "main" not in self._cache:
                            self._cache["main"] = {}
                        self._cache["main"].update(legacy_config)
                        self._last_modified["main"] = datetime.now()
                        
                        # 保存新配置
                        self.save("main")
                        
                        # 备份旧配置
                        backup_path = legacy_path.with_suffix(".json.bak")
                        legacy_path.rename(backup_path)
                        
                        print(f"✓ 已迁移旧配置：{legacy_path} -> {CONFIG_ROOT}/main.json")
                        print(f"  旧配置备份：{backup_path}")
                    
                    self._migrated_legacy = True
                    break
                    
                except Exception as e:
                    print(f"⚠️  迁移旧配置失败 {legacy_path}: {e}")
    
    def get(self, module_name: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取配置
        
        参数:
            module_name: 模块名称（如 "app", "database"）
            key: 配置键（可选）
            default: 默认值
        
        返回:
            配置值
        """
        # 懒加载 - 如果缓存中没有，尝试从文件加载
        if module_name not in self._cache:
            file_path = CONFIG_ROOT / f"{module_name}.json"
            if file_path.exists():
                self._load_file(module_name, file_path)
            else:
                self._cache[module_name] = {}
        
        config = self._cache[module_name]
        
        if key is not None:
            return config.get(key, default)
        
        return config
    
    def set(self, module_name: str, key: str, value: Any, save: bool = True):
        """
        设置配置项
        
        参数:
            module_name: 模块名称
            key: 配置键
            value: 配置值
            save: 是否立即保存到文件
        """
        if module_name not in self._cache:
            self._cache[module_name] = {}
        
        self._cache[module_name][key] = value
        self._last_modified[module_name] = datetime.now()
        
        # 触发回调
        self._trigger_callbacks(module_name, key, value)
        
        if save:
            self.save(module_name)
    
    def set_all(self, module_name: str, config: Dict[str, Any], save: bool = True):
        """
        设置整个模块的配置
        
        参数:
            module_name: 模块名称
            config: 配置字典
            save: 是否立即保存到文件
        """
        self._cache[module_name] = config.copy()
        self._last_modified[module_name] = datetime.now()
        
        if save:
            self.save(module_name)
    
    def save(self, module_name: str):
        """
        保存模块配置到文件
        
        参数:
            module_name: 模块名称
        """
        if module_name not in self._cache:
            return
        
        file_path = CONFIG_ROOT / f"{module_name}.json"
        config = self._cache[module_name]
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存配置
        file_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        # 设置文件权限（仅所有者可读写）
        os.chmod(file_path, 0o600)
        
        self._file_paths[module_name] = file_path
    
    def save_all(self):
        """保存所有模块的配置到文件"""
        for module_name in list(self._cache.keys()):
            self.save(module_name)
    
    def has(self, module_name: str, key: Optional[str] = None) -> bool:
        """
        检查配置是否存在
        
        参数:
            module_name: 模块名称
            key: 配置键（可选）
        
        返回:
            是否存在
        """
        if module_name not in self._cache:
            file_path = CONFIG_ROOT / f"{module_name}.json"
            if file_path.exists():
                self._load_file(module_name, file_path)
            else:
                return False
        
        if key is not None:
            return key in self._cache[module_name]
        
        return len(self._cache[module_name]) > 0
    
    def delete(self, module_name: str, key: Optional[str] = None, save: bool = True):
        """
        删除配置
        
        参数:
            module_name: 模块名称
            key: 配置键（可选，不传则删除整个模块配置）
            save: 是否立即保存到文件
        """
        if module_name not in self._cache:
            return
        
        if key is not None:
            if key in self._cache[module_name]:
                del self._cache[module_name][key]
        else:
            del self._cache[module_name]
        
        if save and key is not None:
            self.save(module_name)
    
    def clear(self, module_name: Optional[str] = None):
        """
        清除缓存
        
        参数:
            module_name: 模块名称（可选，不传则清除所有）
        """
        if module_name is not None:
            self._cache.pop(module_name, None)
        else:
            self._cache.clear()
    
    def reload(self, module_name: str) -> Dict[str, Any]:
        """
        从文件重新加载配置（忽略缓存）
        
        参数:
            module_name: 模块名称
        
        返回:
            配置字典
        """
        file_path = CONFIG_ROOT / f"{module_name}.json"
        if file_path.exists():
            return self._load_file(module_name, file_path)
        return {}
    
    def register_callback(self, module_name: str, callback: Callable):
        """
        注册配置变更回调
        
        参数:
            module_name: 模块名称
            callback: 回调函数 (module_name, key, value)
        """
        if module_name not in self._callbacks:
            self._callbacks[module_name] = []
        self._callbacks[module_name].append(callback)
    
    def _trigger_callbacks(self, module_name: str, key: str, value: Any):
        """触发配置变更回调"""
        if module_name in self._callbacks:
            for callback in self._callbacks[module_name]:
                try:
                    callback(module_name, key, value)
                except Exception as e:
                    print(f"⚠️  配置回调执行失败：{e}")
    
    def list_modules(self) -> List[str]:
        """
        列出所有已加载的模块
        
        返回:
            模块名称列表
        """
        if CONFIG_ROOT.exists():
            for config_file in CONFIG_ROOT.glob("*.json"):
                module_name = config_file.stem
                if module_name.startswith("_"):
                    continue
                if module_name not in self._cache:
                    self._load_file(module_name, config_file)
        
        return list(self._cache.keys())
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模块的配置
        
        返回:
            所有配置
        """
        return self._cache.copy()
    
    def get_config_path(self, module_name: str) -> Path:
        """
        获取模块配置文件路径
        
        参数:
            module_name: 模块名称
        
        返回:
            配置文件路径
        """
        return CONFIG_ROOT / f"{module_name}.json"
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """获取单例实例"""
        return cls()
    
    def __repr__(self) -> str:
        return f"ConfigManager(modules={list(self._cache.keys())})"


# 便捷函数 - 无需创建实例即可使用
def get_config(module_name: str, key: Optional[str] = None, default: Any = None) -> Any:
    """获取配置（便捷函数）"""
    return ConfigManager.get_instance().get(module_name, key, default)


def set_config(module_name: str, key: str, value: Any, save: bool = True):
    """设置配置（便捷函数）"""
    ConfigManager.get_instance().set(module_name, key, value, save)


def set_all_config(module_name: str, config: Dict[str, Any], save: bool = True):
    """设置整个模块配置（便捷函数）"""
    ConfigManager.get_instance().set_all(module_name, config, save)


def save_config(module_name: str):
    """保存配置（便捷函数）"""
    ConfigManager.get_instance().save(module_name)


def has_config(module_name: str, key: Optional[str] = None) -> bool:
    """检查配置是否存在（便捷函数）"""
    return ConfigManager.get_instance().has(module_name, key)


# 模块级单例缓存（供模块内部使用）
_module_cache: Dict[str, Any] = {}


def get_module_config(module_name: str) -> Dict[str, Any]:
    """
    获取模块配置（带本地缓存）
    
    这个函数适合在模块内部使用，避免每次都通过 ConfigManager 获取
    
    参数:
        module_name: 模块名称
    
    返回:
        配置字典
    """
    if module_name not in _module_cache:
        _module_cache[module_name] = get_config(module_name)
    return _module_cache[module_name]


def invalidate_module_cache(module_name: str):
    """
    使模块缓存失效
    
    参数:
        module_name: 模块名称
    """
    _module_cache.pop(module_name, None)


# 初始化全局单例
_global_config: Optional[ConfigManager] = None


def init_global_config() -> ConfigManager:
    """
    初始化全局配置实例
    
    返回:
        ConfigManager 实例
    """
    global _global_config
    _global_config = ConfigManager.get_instance()
    return _global_config


def get_global_config() -> ConfigManager:
    """
    获取全局配置实例
    
    返回:
        ConfigManager 实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager.get_instance()
    return _global_config


# CLI 测试入口
if __name__ == "__main__":
    import sys
    
    config = ConfigManager.get_instance()
    
    if len(sys.argv) < 2:
        print("用法：python config.py <command> [args]")
        print("命令：")
        print("  list                  - 列出所有模块")
        print("  get <module> [key]    - 获取配置")
        print("  set <module> <key> <value> - 设置配置")
        print("  save <module>         - 保存配置")
        print("  reload <module>       - 重新加载配置")
        print("  path <module>         - 显示配置文件路径")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        modules = config.list_modules()
        print(f"已加载的模块 ({len(modules)}):")
        for module in modules:
            print(f"  - {module}")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("用法：python config.py get <module> [key]")
            sys.exit(1)
        module = sys.argv[2]
        key = sys.argv[3] if len(sys.argv) > 3 else None
        result = config.get(module, key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "set":
        if len(sys.argv) < 5:
            print("用法：python config.py set <module> <key> <value>")
            sys.exit(1)
        module = sys.argv[2]
        key = sys.argv[3]
        value = sys.argv[4]
        try:
            value = json.loads(value)
        except:
            pass
        config.set(module, key, value)
        print(f"✓ 已设置 {module}.{key} = {value}")
    
    elif command == "save":
        if len(sys.argv) < 3:
            print("用法：python config.py save <module>")
            sys.exit(1)
        module = sys.argv[2]
        config.save(module)
        print(f"✓ 已保存 {module} 配置")
    
    elif command == "reload":
        if len(sys.argv) < 3:
            print("用法：python config.py reload <module>")
            sys.exit(1)
        module = sys.argv[2]
        result = config.reload(module)
        print(f"✓ 已重新加载 {module} 配置")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "path":
        if len(sys.argv) < 3:
            print("用法：python config.py path <module>")
            sys.exit(1)
        module = sys.argv[2]
        path = config.get_config_path(module)
        print(f"配置文件：{path}")
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)
