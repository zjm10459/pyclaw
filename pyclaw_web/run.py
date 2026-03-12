#!/usr/bin/env python3
"""
PyClaw Web 启动入口
"""

import os
import sys
from pathlib import Path

def main():
    """PyClaw Web 命令行入口"""
    # 找到 pyclaw-web 目录
    current_dir = Path(__file__).parent
    web_dir = current_dir.parent / "pyclaw-web"
    
    if not web_dir.exists():
        print(f"❌ 错误：pyclaw-web 目录不存在")
        print(f"   期望位置：{web_dir}")
        sys.exit(1)
    
    # 切换到 pyclaw-web 目录
    os.chdir(web_dir)
    
    # 添加路径
    sys.path.insert(0, str(web_dir))
    
    # 设置环境变量
    host = os.getenv("PYCLAW_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("PYCLAW_WEB_PORT", "18800"))
    
    print(f"🦮 PyClaw Web 启动中...")
    print(f"   访问：http://{host}:{port}")
    print(f"   按 Ctrl+C 停止")
    print()
    
    # 启动应用
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
