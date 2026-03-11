"""
技能加载器（兼容 AgentSkills 格式）
====================================

参考 OpenClaw 的技能系统：
- AgentSkills 兼容格式（SKILL.md + YAML frontmatter）
- 技能 gating（基于环境、配置、二进制文件、操作系统）
- 多位置加载（bundled/managed/workspace）
- ClawHub 集成准备
- Windows/Linux 自动识别

格式示例：
```markdown
---
name: web-search
description: 搜索网络
metadata: {"openclaw": {"requires": {"env": ["BRAVE_API_KEY"]}}}
---

# Web Search Skill

使用 Brave Search API 搜索网络...
```

操作系统识别：
- 自动检测 Windows/Linux/macOS
- 技能可根据 OS 启用/禁用
- 支持路径分隔符自动适配
"""

import os
import re
import json
import logging
import shutil
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import yaml

logger = logging.getLogger("pyclaw.skills")


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    description: str
    homepage: Optional[str] = None
    emoji: Optional[str] = None
    user_invocable: bool = True
    disable_model_invocation: bool = False
    requires: Dict[str, Any] = field(default_factory=dict)
    install: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_frontmatter(cls, frontmatter: Dict[str, Any]) -> 'SkillMetadata':
        """从 frontmatter 创建元数据"""
        return cls(
            name=frontmatter.get("name", "unknown"),
            description=frontmatter.get("description", ""),
            homepage=frontmatter.get("homepage"),
            emoji=frontmatter.get("emoji"),
            user_invocable=frontmatter.get("user-invocable", True),
            disable_model_invocation=frontmatter.get("disable-model-invocation", False),
            requires=frontmatter.get("metadata", {}).get("openclaw", {}).get("requires", {}),
            install=frontmatter.get("metadata", {}).get("openclaw", {}).get("install"),
        )


@dataclass
class Skill:
    """技能定义（惰性加载内容）"""
    name: str
    path: Path
    metadata: SkillMetadata
    enabled: bool = True
    
    # 惰性加载的字段
    _content: Optional[str] = None
    _instructions: Optional[str] = None
    _loaded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（只包含元数据）"""
        return {
            "name": self.name,
            "path": str(self.path),
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "homepage": self.metadata.homepage,
                "emoji": self.metadata.emoji,
            },
            "enabled": self.enabled,
        }
    
    def _load_content(self):
        """惰性加载文件内容"""
        if self._loaded:
            return
        
        skill_md = self.path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            _, instructions = self._parse_frontmatter(content)
            self._content = content
            self._instructions = instructions
        
        self._loaded = True
    
    @staticmethod
    def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """解析 frontmatter（静态方法，避免循环导入）"""
        import re
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        
        if not match:
            return {}, content
        
        yaml_text = match.group(1)
        instructions = match.group(2).strip()
        
        try:
            import yaml
            frontmatter = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            frontmatter = {}
        
        return frontmatter, instructions
    
    @property
    def content(self) -> Optional[str]:
        """惰性加载 content"""
        self._load_content()
        return self._content
    
    @property
    def instructions(self) -> Optional[str]:
        """惰性加载 instructions"""
        self._load_content()
        return self._instructions


class SkillLoader:
    """
    技能加载器
    
    功能：
    - 从多个位置加载技能
    - 解析 SKILL.md 文件
    - 根据 gating 规则过滤技能
    - 支持热重载
    """
    
    def __init__(self, workspace: Optional[str] = None):
        """
        初始化技能加载器
        
        自动检测操作系统并记录。
        
        参数:
            workspace: 工作区路径
        """
        self.workspace = Path(workspace or Path.home() / ".pyclaw" / "workspace").expanduser()
        
        # 检测操作系统
        self.os_name = self._get_os_name()
        self.os_arch = platform.machine()
        
        logger.info(f"技能加载器初始化：操作系统={self.os_name}, 架构={self.os_arch}")
        
        # 技能加载位置（优先级从高到低）
        self.skill_dirs = [
            self.workspace / "skills",  # 工作区技能（最高优先级）
            Path.home() / ".pyclaw" / "skills",  # 管理技能
            Path.home() / ".pyclaw" / "bundled-skills",  # 捆绑技能（最低优先级）
        ]
        
        # 已加载的技能
        self.skills: Dict[str, Skill] = {}
        
        # 加载技能
        self._load_all_skills()
        
        logger.info(f"技能加载完成：{len(self.skills)} 个技能可用")
    
    def _load_all_skills(self):
        """从所有位置加载技能"""
        loaded_names = set()
        
        # 按优先级加载（高优先级覆盖低优先级）
        for skill_dir in reversed(self.skill_dirs):
            if not skill_dir.exists():
                continue
            
            for skill_path in skill_dir.iterdir():
                if not skill_path.is_dir():
                    continue
                
                skill_md = skill_path / "SKILL.md"
                if not skill_md.exists():
                    continue
                
                try:
                    skill = self._load_skill(skill_path, skill_md)
                    
                    # 检查 gating
                    if self._check_gating(skill):
                        # 高优先级覆盖
                        if skill.name not in loaded_names:
                            self.skills[skill.name] = skill
                            loaded_names.add(skill.name)
                            logger.debug(f"加载技能：{skill.name}")
                        else:
                            logger.debug(f"跳过技能（已加载）：{skill.name}")
                    else:
                        logger.debug(f"技能未通过 gating：{skill.name}")
                
                except Exception as e:
                    logger.error(f"加载技能失败 {skill_path}: {e}")
    
    def _load_skill(self, path: Path, skill_md: Path) -> Skill:
        """
        加载单个技能（只加载元数据）
        
        参数:
            path: 技能目录
            skill_md: SKILL.md 文件路径
        
        返回:
            Skill 对象（内容惰性加载）
        """
        # 只读取文件解析 frontmatter，不存储完整内容
        content = skill_md.read_text(encoding='utf-8')
        frontmatter, _ = self._parse_frontmatter(content)
        
        # 创建元数据
        metadata = SkillMetadata.from_frontmatter(frontmatter)
        
        # 创建 Skill 对象（不加载 content 和 instructions）
        return Skill(
            name=metadata.name,
            path=path,
            metadata=metadata,
            # content 和 instructions 会在首次访问时惰性加载
        )
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        解析 YAML frontmatter
        
        参数:
            content: 文件内容
        
        返回:
            (frontmatter 字典，指令内容)
        """
        # 匹配 frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        
        if not match:
            return {}, content
        
        yaml_text = match.group(1)
        instructions = match.group(2).strip()
        
        try:
            frontmatter = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as e:
            logger.error(f"解析 frontmatter 失败：{e}")
            frontmatter = {}
        
        return frontmatter, instructions
    
    def _check_gating(self, skill: Skill) -> bool:
        """
        检查技能 gating 规则
        
        支持以下 gating 条件：
        - always: 总是启用
        - os: 操作系统列表（windows, linux, darwin）
        - bins: 必需的二进制文件
        - env: 必需的环境变量
        - config: 配置要求
        - arch: CPU 架构（x86_64, arm64 等）
        
        参数:
            skill: 技能对象
        
        返回:
            True（通过）或 False（不通过）
        """
        requires = skill.metadata.requires
        
        # 检查 always - 总是启用
        if requires.get("always"):
            return True
        
        # ========== 操作系统识别 ==========
        if "os" in requires:
            current_os = self._get_os_name()
            allowed_os = [o.lower() for o in requires["os"]]
            
            if current_os not in allowed_os:
                logger.debug(f"技能 {skill.name} 不支持当前操作系统：{current_os} (要求：{allowed_os})")
                return False
            
            logger.debug(f"技能 {skill.name} 操作系统检查通过：{current_os}")
        
        # ========== CPU 架构检查 ==========
        if "arch" in requires:
            current_arch = platform.machine().lower()
            allowed_arch = [a.lower() for a in requires["arch"]]
            
            if current_arch not in allowed_arch:
                logger.debug(f"技能 {skill.name} 不支持当前 CPU 架构：{current_arch} (要求：{allowed_arch})")
                return False
        
        # ========== 二进制文件检查 ==========
        if "bins" in requires:
            for binary in requires["bins"]:
                if not shutil.which(binary):
                    logger.debug(f"技能 {skill.name} 缺少二进制文件：{binary}")
                    return False
        
        # ========== 环境变量检查 ==========
        if "env" in requires:
            for env_var in requires["env"]:
                # 支持 ${VAR_NAME} 格式
                if env_var.startswith("${") and env_var.endswith("}"):
                    env_var = env_var[2:-1]
                
                if env_var not in os.environ or not os.environ[env_var]:
                    logger.debug(f"技能 {skill.name} 缺少环境变量：{env_var}")
                    return False
        
        # ========== 配置文件检查 ==========
        if "config" in requires:
            # TODO: 加载配置并检查
            pass
        
        # ========== 路径存在性检查 ==========
        if "paths" in requires:
            for path in requires["paths"]:
                # 自动适配 Windows/Linux 路径分隔符
                path = self._adapt_path(path)
                if not Path(path).exists():
                    logger.debug(f"技能 {skill.name} 缺少必需路径：{path}")
                    return False
        
        return True
    
    def _get_os_name(self) -> str:
        """
        获取标准化的操作系统名称
        
        返回:
            小写的操作系统名称：windows, linux, darwin
        """
        system = platform.system().lower()
        
        # 标准化映射
        os_map = {
            "windows": "windows",
            "linux": "linux",
            "darwin": "darwin",  # macOS
            "macos": "darwin",
        }
        
        return os_map.get(system, system)
    
    def _adapt_path(self, path: str) -> str:
        """
        根据操作系统自动适配路径
        
        支持以下格式：
        - Unix 风格：/home/user/.pyclaw
        - Windows 风格：C:\\Users\\user\\.pyclaw
        - 通用格式：~/.pyclaw (自动展开)
        
        参数:
            path: 原始路径
        
        返回:
            适配后的路径
        """
        # 展开 ~
        if path.startswith("~"):
            path = os.path.expanduser(path)
        
        # 检测当前操作系统
        current_os = self._get_os_name()
        
        if current_os == "windows":
            # Windows: 转换路径分隔符
            path = path.replace("/", "\\")
        else:
            # Unix-like (Linux/macOS): 转换路径分隔符
            path = path.replace("\\", "/")
        
        return path
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list_skills(self, enabled_only: bool = True) -> List[Skill]:
        """
        列出技能
        
        参数:
            enabled_only: 是否只列出启用的技能
        
        返回:
            技能列表
        """
        skills = list(self.skills.values())
        
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        
        return skills
    
    def get_skill_instructions(self, name: str) -> Optional[str]:
        """获取技能指令（惰性加载）"""
        skill = self.get_skill(name)
        if skill:
            return skill.instructions  # 首次访问时自动加载
        return None
    
    def get_skills_prompt(self) -> str:
        """
        生成技能提示词（惰性加载）
        
        只在需要时才读取文件内容。
        
        返回:
            所有技能的指令文本
        """
        prompts = []
        
        for skill in self.list_skills():
            if not skill.metadata.disable_model_invocation:
                instructions = skill.instructions  # 惰性加载
                if instructions:
                    prompts.append(f"# {skill.name}\n\n{instructions}\n")
        
        return "\n---\n\n".join(prompts)
    
    def reload(self):
        """重新加载技能"""
        self.skills.clear()
        self._load_all_skills()
        logger.info(f"技能重新加载完成：{len(self.skills)} 个技能")


# 全局实例
_default_loader: Optional[SkillLoader] = None

def get_skill_loader(workspace: Optional[str] = None) -> SkillLoader:
    """获取全局技能加载器"""
    global _default_loader
    if _default_loader is None:
        _default_loader = SkillLoader(workspace)
    return _default_loader
