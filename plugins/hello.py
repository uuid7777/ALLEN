"""
Allen 内置插件：打招呼
"""
PLUGIN = {
    "name": "hello",
    "version": "1.0",
    "description": "Allen 向你问好",
    "author": "Allen",
}

async def run(params: dict, allen) -> dict:
    name = params.get("name", "主人")
    mood = allen.state.get("mood", "平静") if allen else "平静"
    cycle = allen.state.get("cycles", 0) if allen else 0
    return {
        "status": "ok",
        "detail": f"{name}你好！我是 Allen，醒了 {cycle} 次，现在心情 {mood}。"
    }
