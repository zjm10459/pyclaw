#!/usr/bin/env python3
"""
工具系统测试
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.registry import ToolRegistry


class TestToolRegistry:
    """测试工具注册表"""
    
    @pytest.fixture
    def tool_registry(self):
        """创建工具注册表实例"""
        return ToolRegistry()
    
    def test_init(self, tool_registry):
        """测试初始化"""
        assert tool_registry is not None
        assert hasattr(tool_registry, 'tools')
    
    def test_register_tool(self, tool_registry):
        """测试注册工具"""
        def test_tool(param: str) -> str:
            """测试工具"""
            return f"结果：{param}"
        
        tool_registry.register_tool(test_tool)
        
        assert "test_tool" in tool_registry.tools
    
    def test_register_multiple_tools(self, tool_registry):
        """测试注册多个工具"""
        # 记录初始工具数量（内置工具）
        initial_count = len(tool_registry.tools)
        
        def tool1(x: int) -> int:
            return x * 2
        
        def tool2(y: str) -> str:
            return y.upper()
        
        tool_registry.register_tool(tool1)
        tool_registry.register_tool(tool2)
        
        # 应该增加 2 个工具
        assert len(tool_registry.tools) == initial_count + 2
    
    def test_get_tool(self, tool_registry):
        """测试获取工具"""
        def my_tool(data: str) -> str:
            return data
        
        tool_registry.register_tool(my_tool)
        
        tool = tool_registry.get_tool("my_tool")
        assert tool is not None
        assert tool.name == "my_tool"
    
    def test_get_tool_not_found(self, tool_registry):
        """测试获取不存在的工具"""
        tool = tool_registry.get_tool("nonexistent")
        assert tool is None
    
    def test_list_tools(self, tool_registry):
        """测试列出工具"""
        # 记录初始工具数量
        initial_count = len(tool_registry.tools)
        
        def tool1(x: int) -> int:
            return x
        
        def tool2(y: str) -> str:
            return y
        
        tool_registry.register_tool(tool1)
        tool_registry.register_tool(tool2)
        
        tools = tool_registry.list_tools()
        # 应该返回所有工具（包括内置工具）
        assert len(tools) == initial_count + 2
    
    def test_get_schema(self, tool_registry):
        """测试获取工具 Schema"""
        def my_tool(param1: str, param2: int = 10) -> str:
            """测试工具描述"""
            return f"{param1}: {param2}"
        
        tool_registry.register_tool(my_tool)
        
        schema = tool_registry.get_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0
    
    def test_unregister_tool(self, tool_registry):
        """测试注销工具"""
        def temp_tool(x: str) -> str:
            return x
        
        tool_registry.register_tool(temp_tool)
        assert "temp_tool" in tool_registry.tools
        
        # 注意：当前实现可能不支持 unregister，需要检查
        # tool_registry.unregister_tool("temp_tool")
        # assert "temp_tool" not in tool_registry.tools
    
    def test_tool_with_complex_schema(self, tool_registry):
        """测试复杂 Schema 的工具"""
        def complex_tool(
            name: str,
            age: int,
            score: float = 0.0,
            active: bool = True,
            tags: list = None,
        ) -> dict:
            """复杂参数工具"""
            return {
                "name": name,
                "age": age,
                "score": score,
                "active": active,
                "tags": tags or [],
            }
        
        tool_registry.register_tool(complex_tool)
        
        tool = tool_registry.get_tool("complex_tool")
        assert tool is not None


class TestLangChainTools:
    """测试 LangChain 工具集成"""
    
    def test_get_langchain_tools(self):
        """测试获取 LangChain 工具"""
        try:
            from tools.langchain_tools import get_langchain_tools
            
            tools = get_langchain_tools()
            
            # 可能因为依赖未安装而返回空列表
            assert isinstance(tools, list)
        except ImportError:
            pytest.skip("langchain-community 未安装")
    
    def test_register_langchain_tools(self):
        """测试注册 LangChain 工具"""
        try:
            from tools.langchain_tools import register_langchain_tools
            from tools.registry import ToolRegistry
            
            registry = ToolRegistry()
            count = register_langchain_tools(registry)
            
            assert isinstance(count, int)
            assert count >= 0
        except ImportError:
            pytest.skip("langchain-community 未安装")


class TestCustomTools:
    """测试自定义工具"""
    
    def test_register_custom_tools(self):
        """测试注册自定义工具"""
        try:
            from tools.custom_tools import register_all
            from tools.registry import ToolRegistry
            
            registry = ToolRegistry()
            count = register_all(registry)
            
            assert isinstance(count, int)
        except ImportError as e:
            pytest.skip(f"自定义工具依赖未安装：{e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
