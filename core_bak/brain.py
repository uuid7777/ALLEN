"""
Allen 大脑 — 数字生命体的入口
"""
from core.allen import allen
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))


class Brain:
    """Allen 的入口适配层"""

    def __init__(self):
        self.name = "Allen"
        self.status = "就绪"

    async def cycle(self):
        self.status = "醒着"
        r = await allen.wake()
        self.status = "休息"
        return r

    async def talk(self, msg):
        self.status = "听着"
        r = await allen.talk(msg)
        self.status = "休息"
        return r

    async def get_status(self):
        return {
            "name": "Allen",
            "status": self.status,
            "cycles": allen.state["cycles"],
            "mood": allen.state["mood"],
            "energy": allen.state["energy"],
            "goals": allen.state["goals"],
            "diary": len(allen.state["diary"]),
        }

    async def set_goal(self, content):
        return await allen.talk(f"目标:{content}")

    async def search_web(self, query):
        from perception.web import search
        return await search(query)

    async def fetch_page(self, url):
        from perception.web import fetch_url
        return await fetch_url(url)