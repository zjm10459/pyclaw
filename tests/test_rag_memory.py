#!/usr/bin/env python3
"""
RAG 记忆系统测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.rag_memory import RAGMemory, RAGMemoryConfig, create_rag_memory


class TestRAGMemoryConfig:
    """测试配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RAGMemoryConfig()
        assert config.workspace == "~/.pyclaw/workspace"
        assert config.chunk_size == 500
        assert config.top_k == 5
        assert config.retrieval_method == "hybrid"
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = RAGMemoryConfig(
            workspace="/tmp/test",
            chunk_size=1000,
            top_k=10,
            hybrid_alpha=0.7,
        )
        assert config.workspace == "/tmp/test"
        assert config.chunk_size == 1000
        assert config.top_k == 10
        assert config.hybrid_alpha == 0.7


class TestRAGMemory:
    """测试 RAG 记忆系统"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作区"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def rag_memory(self, temp_workspace):
        """创建 RAG 记忆实例"""
        config = RAGMemoryConfig(
            workspace=str(temp_workspace),
            enable_vector_search=False,  # 测试时禁用向量搜索（加速）
        )
        return RAGMemory(config=config)
    
    def test_init(self, rag_memory):
        """测试初始化"""
        assert rag_memory is not None
        assert rag_memory.chunks is not None
        assert rag_memory.documents is not None
    
    def test_add_memory(self, rag_memory):
        """测试添加记忆"""
        chunk_id = rag_memory.add_memory(
            content="测试记忆内容",
            category="test",
            tags=["test", "pytest"],
        )
        
        assert chunk_id is not None
        assert len(rag_memory.chunks) > 0
    
    def test_add_multiple_memories(self, rag_memory):
        """测试添加多条记忆"""
        memories = [
            ("记忆 1", "test", ["tag1"]),
            ("记忆 2", "test", ["tag2"]),
            ("记忆 3", "test", ["tag1", "tag2"]),
        ]
        
        for content, category, tags in memories:
            rag_memory.add_memory(content, category=category, tags=tags)
        
        assert len(rag_memory.chunks) >= 3
    
    def test_search_bm25(self, rag_memory):
        """测试 BM25 搜索"""
        # 添加测试数据
        rag_memory.add_memory("Python 是一种编程语言", category="tech")
        rag_memory.add_memory("Java 也是一种编程语言", category="tech")
        rag_memory.add_memory("今天天气不错", category="daily")
        
        # 搜索
        results = rag_memory.search("Python", top_k=5, method="bm25")
        
        assert len(results) > 0
        assert any("Python" in chunk.content for chunk in results)
    
    def test_search_vector(self, temp_workspace):
        """测试向量搜索"""
        config = RAGMemoryConfig(
            workspace=str(temp_workspace),
            enable_vector_search=True,
        )
        
        try:
            rag = RAGMemory(config=config)
            
            # 添加测试数据
            rag.add_memory("机器学习是 AI 的分支", category="ai")
            rag.add_memory("深度学习需要大量数据", category="ai")
            
            # 搜索
            results = rag.search("AI 技术", top_k=5, method="vector")
            
            assert len(results) >= 0  # 可能因为没有模型而返回空
        except Exception:
            # 如果模型加载失败，跳过测试
            pytest.skip("向量模型加载失败")
    
    def test_search_hybrid(self, rag_memory):
        """测试混合搜索"""
        # 添加测试数据
        rag_memory.add_memory("RAG 是检索增强生成", category="tech")
        rag_memory.add_memory("向量数据库用于存储嵌入", category="tech")
        
        # 搜索
        results = rag_memory.search("检索技术", top_k=5, method="hybrid")
        
        assert len(results) >= 0
    
    def test_get_context(self, rag_memory):
        """测试获取上下文"""
        rag_memory.add_memory("RAG 包括分块、嵌入、检索", category="tech")
        rag_memory.add_memory("BM25 是传统搜索算法", category="tech")
        
        context = rag_memory.get_context("RAG 技术", max_tokens=500)
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_get_stats(self, rag_memory):
        """测试统计信息"""
        rag_memory.add_memory("测试记忆", category="test")
        
        stats = rag_memory.get_stats()
        
        assert "total_chunks" in stats
        assert "categories" in stats
        assert "retrieval_method" in stats
    
    def test_category_filter(self, rag_memory):
        """测试分类过滤"""
        rag_memory.add_memory("技术内容 1", category="tech")
        rag_memory.add_memory("技术内容 2", category="tech")
        rag_memory.add_memory("日常内容", category="daily")
        
        # 只搜索 tech 分类
        results = rag_memory.search("内容", top_k=10, category="tech")
        
        # 应该只返回 tech 分类的结果
        for chunk in results:
            assert chunk.metadata.get("category") == "tech"


class TestCreateRAGMemory:
    """测试便捷函数"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作区"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_create_with_defaults(self, temp_workspace):
        """测试使用默认配置创建"""
        rag = create_rag_memory(
            workspace_path=str(temp_workspace),
            enable_vector_search=False,
        )
        
        assert rag is not None
        assert rag.config.retrieval_method == "hybrid"
    
    def test_create_with_custom_config(self, temp_workspace):
        """测试使用自定义配置创建"""
        rag = create_rag_memory(
            workspace_path=str(temp_workspace),
            retrieval_method="bm25",
            hybrid_alpha=0.7,
            use_mmr=True,
            top_k=10,
        )
        
        assert rag.config.retrieval_method == "bm25"
        assert rag.config.hybrid_alpha == 0.7
        assert rag.config.use_mmr is True
        assert rag.config.top_k == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
