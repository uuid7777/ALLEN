"""
Allen 进化循环
============
自我改进的核心引擎。定期运行，分析 Allen 的状态并提出改进。
"""
import os
import json
from datetime import datetime
from core.llm import llm
from evolution.meta import MetaAgent
from evolution.improve import analyze_and_improve, log_action
from evolution.archive import (
    record_generation, snapshot, select_parent,
    get_generation_count, get_best_gen, get_evolution_tree
)
from instincts import instincts
from core.heartbeat import beat


EVOLUTION_LOG = "D:\\EVA\\evolution_log"
CORE_FILES = [
    "D:\\EVA\\chat_server.py",
    "D:\\EVA\\core\\allen.py",
    "D:\\EVA\\core\\brain.py",
]


def evolution_cycle(domain: str = "life", force: bool = False):
    """一次完整的进化循环"""
    gen_id = f"gen_{get_generation_count() + 1:04d}"
    parent_id = select_parent()

    print(f"\n{'='*50}")
    print(f"[进化] 第 {get_generation_count() + 1} 代 | {gen_id}")
    print(f"[进化] 父代: {parent_id or '首次进化'}")
    print(f"{'='*50}")

    # 1. 心跳
    beat()

    # 2. 健康检查
    health = instincts.check_existence()
    if not health["healthy"]:
        print(f"[进化] ⚠ 健康检查失败，跳过")
        return False

    # 3. 快照当前代码（备份，用于回滚）
    snapshot(CORE_FILES, gen_id)

    # 4. 分析并改进
    result = analyze_and_improve()

    # 5. 评分（1-10，基于代码是否健康）
    score = 5.0  # 基准分
    if result:
        score += 2.0  # 成功改进加分

    # 6. 记录到档案
    record_generation(
        gen_id=gen_id,
        parent_id=parent_id,
        score=score,
        changes=[{"result": str(result)}],
    )

    # 7. 输出进化树
    tree = get_evolution_tree()
    print(f"\n[进化] 当前进化代数: {len(tree)}")
    print(f"[进化] 最高分版本: {get_best_gen() or '无'}")

    return True


def run(target_iterations: int = 1):
    """运行进化循环"""
    for i in range(target_iterations):
        print(f"\n{'='*40}")
        print(f"[EVOLUTION] 第 {i+1}/{target_iterations} 次迭代")
        print(f"{'='*40}")
        if not evolution_cycle():
            print(f"[EVOLUTION] ❌ 第 {i+1} 次迭代失败")
            break
    print("[EVOLUTION] ✅ 进化完成")


if __name__ == "__main__":
    run()
