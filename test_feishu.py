#!/usr/bin/env python3
"""
飞书渠道测试脚本
=================

测试飞书渠道的基本功能。

使用方式:
    python test_feishu.py --app-id cli_xxx --app-secret xxx
"""

import asyncio
import argparse
import logging
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="测试飞书渠道")
    
    parser.add_argument(
        "--app-id",
        required=True,
        help="飞书 App ID",
    )
    parser.add_argument(
        "--app-secret",
        required=True,
        help="飞书 App Secret",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=18790,
        help="Webhook 监听端口",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细输出",
    )
    
    return parser.parse_args()


async def test_token(app_id: str, app_secret: str):
    """测试获取访问令牌"""
    import requests
    
    print("🔑 测试获取访问令牌...")
    
    try:
        response = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
            json={
                "app_id": app_id,
                "app_secret": app_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") == 0:
            print(f"✓ 令牌获取成功")
            print(f"  Token: {data['app_access_token'][:20]}...")
            print(f"  过期时间：{data.get('expire', 'N/A')} 秒")
            return data["app_access_token"]
        else:
            print(f"✗ 令牌获取失败：{data}")
            return None
            
    except Exception as e:
        print(f"✗ 异常：{e}")
        return None


async def test_webhook_server(port: int):
    """测试 Webhook 服务器"""
    from aiohttp import web
    
    print(f"\n🌐 启动 Webhook 服务器 (端口 {port})...")
    
    async def handle_webhook(request: web.Request) -> web.Response:
        try:
            body = await request.json()
            event_type = body.get("header", {}).get("event_type", "unknown")
            
            print(f"✓ 收到事件：{event_type}")
            
            # 处理验证
            if event_type == "url_verification":
                challenge = body.get("challenge")
                print(f"  验证挑战：{challenge}")
                return web.json_response({"challenge": challenge})
            
            # 处理消息
            if event_type == "im.message.receive_v1":
                message = body.get("event", {}).get("message", {})
                sender = body.get("event", {}).get("sender", {})
                
                content = message.get("content", "{}")
                import json
                content_text = json.loads(content).get("text", content)
                
                print(f"  消息：{sender.get('sender_name')} - {content_text[:50]}")
            
            return web.json_response({"status": "success"})
            
        except Exception as e:
            print(f"✗ 处理事件失败：{e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_health(request: web.Request) -> web.Response:
        return web.json_response({
            "status": "ok",
            "channel": "feishu",
            "test": True,
        })
    
    app = web.Application()
    app.router.add_post("/feishu/webhook", handle_webhook)
    app.router.add_get("/feishu/webhook", handle_health)
    app.router.add_get("/health", handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"✓ Webhook 服务器运行中")
    print(f"  URL: http://0.0.0.0:{port}/feishu/webhook")
    print(f"  健康检查：http://localhost:{port}/health")
    print(f"\n按 Ctrl+C 停止\n")
    
    try:
        # 保持运行 30 秒
        await asyncio.sleep(30)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


async def main():
    args = parse_args()
    
    # 设置日志
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)
    
    print("=" * 50)
    print("飞书渠道测试")
    print("=" * 50)
    print()
    
    # 测试 1: 获取令牌
    token = await test_token(args.app_id, args.app_secret)
    
    if not token:
        print("\n✗ 令牌测试失败，请检查 App ID 和 App Secret")
        sys.exit(1)
    
    # 测试 2: Webhook 服务器
    await test_webhook_server(args.port)
    
    print("\n✓ 所有测试完成！")
    print("\n下一步:")
    print("1. 将 Webhook URL 配置到飞书开放平台")
    print("2. 运行 python main_feishu.py 启动完整服务")


if __name__ == "__main__":
    asyncio.run(main())
