"""
Allen 觉醒机制 — 定时自主启动
支持两种模式:
1. 内部循环 (asyncio.sleep) — 开发/测试用
2. Windows 计划任务触发 — 生产环境，每次启动运行一次
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))


class Awakener:
    """Allen 的觉醒调度器"""

    def __init__(self, brain, interval: int = 3600):
        self.brain = brain
        self.interval = interval  # 秒
        self._running = False

    async def run(self):
        """进入生命循环"""
        self._running = True
        print(f"[觉醒] 每 {self.interval}s 自动觉醒一次")
        print("[觉醒] 按 Ctrl+C 休眠\n")

        # 启动后立即执行一次
        await self.brain.cycle()

        while self._running:
            print(f"\n[觉醒] 下次觉醒: {self.interval}s 后...")
            await asyncio.sleep(self.interval)
            await self.brain.cycle()

    def stop(self):
        self._running = False


# === 计划任务模式: 每次运行只执行一次，然后退出 ===
async def run_once():
    """供 Windows 计划任务调用"""
    from core.allen import allen
    result = await allen.wake()
    print(f"\n[计划任务] Allen 醒了一次")
    return result


if __name__ == "__main__":
    # 直接运行此文件 = 计划任务模式
    asyncio.run(run_once())