#!/usr/bin/env python3
"""
PyClaw Web 快速启动脚本
"""

import subprocess
import sys
import os

# 检查并安装依赖
try:
    import fastapi
    import uvicorn
except ImportError:
    print("📦 安装依赖...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "fastapi", "uvicorn[standard]", "python-multipart",
        "aiohttp", "websockets", "jinja2", "python-dotenv",
        "--break-system-packages", "-q"
    ])

# 启动应用
if __name__ == "__main__":
    host = os.getenv("PYCLAW_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("PYCLAW_WEB_PORT", "18800"))
    
    print(f"🦮 PyClaw Web 启动中...")
    print(f"   访问：http://{host}:{port}")
    print(f"   按 Ctrl+C 停止")
    print()
    
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")
