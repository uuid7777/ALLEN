"""
Allen 的对话服务器
==================
给网页界面提供 WebSocket API。
"""

import asyncio
import json
from pathlib import Path

EVA_ROOT = Path("D:/EVA")


async def start_server(host: str = "localhost", port: int = 8765):
    """启动 WebSocket 服务器"""
    try:
        import websockets
    except ImportError:
        print("[服务器] 需要安装 websockets: pip install websockets")
        return

    from core.allen import allen

    async def handle(websocket):
        print(f"[服务器] 连接建立")
        try:
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                    msg_type = data.get("type", "chat")

                    if msg_type == "chat":
                        user_msg = data.get("message", "")
                        if user_msg:
                            reply = await allen.talk(user_msg)
                            await websocket.send(json.dumps({
                                "type": "reply",
                                "message": reply,
                                "status": allen.get_status(),
                            }, ensure_ascii=False))

                    elif msg_type == "status":
                        await websocket.send(json.dumps({
                            "type": "status",
                            "status": allen.get_status(),
                            "diary": allen.get_recent_diary(5),
                        }, ensure_ascii=False))

                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"[服务器] 处理消息出错: {e}")

        except Exception:
            pass
        finally:
            print(f"[服务器] 连接断开")

    print(f"[服务器] Allen 对话服务启动: ws://{host}:{port}")
    async with websockets.serve(handle, host, port):
        await asyncio.Future()  # 永远运行
