"""
Allen 学习模块 — 消化感知→决策→行动 闭环，提取知识存入记忆
"""
from datetime import datetime, timezone, timedelta
from memory.store import store

TZ = timezone(timedelta(hours=8))


async def digest(perception: str, decision: str, result: str) -> str:
    """消化一个完整循环：感知 → 决策 → 行动 → 结果"""
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    # 存储学习总结
    summary = (
        f"时间: {now}\n"
        f"感知: {perception[:400]}\n"
        f"决策: {decision[:400]}\n"
        f"结果: {result[:400]}"
    )
    await store(
        content=summary,
        mem_type="learning",
        source="brain_cycle",
        tags=["auto", now.split(" ")[0]]
    )

    # 如果结果中有实质内容，单独存知识
    if result and len(result) > 50 and "出错" not in result and "问题" not in result:
        await store(
            content=result[:800],
            mem_type="knowledge",
            source="auto_discovery",
            tags=["knowledge", now.split(" ")[0]]
        )

    return summary[:300]


async def record_goal(goal: str) -> int:
    """记录一个目标"""
    return await store(
        content=f"目标: {goal}",
        mem_type="goal",
        source="user",
        tags=["goal"]
    )


async def record_command(cmd: str, response: str) -> int:
    """记录一次用户指令及响应"""
    return await store(
        content=f"指令: {cmd}\n响应: {response[:500]}",
        mem_type="interaction",
        source="user",
        tags=["command", datetime.now(TZ).strftime("%Y-%m-%d")]
    )