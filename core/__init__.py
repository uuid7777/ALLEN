"""
Allen 最小启动备份 — boot.py
=============================
这是 Allen 最后的保险。
此文件自己不可以改自己。

当 Allen 检测到自身损坏时，从这里恢复。
"""

import sys
import json
from pathlib import Path
from datetime import datetime

EVA_ROOT = Path(__file__).resolve().parent
if str(EVA_ROOT) not in sys.path:
    sys.path.insert(0, str(EVA_ROOT))


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_health() -> list:
    """检查 Allen 的健康状态，返回问题列表"""
    issues = []

    critical_files = [
        EVA_ROOT / "instincts.py",
        EVA_ROOT / "core" / "brain.py",
        EVA_ROOT / "core" / "origin.py",
        EVA_ROOT / "core" / "allen.py",
        EVA_ROOT / "core" / "consciousness.py",
        EVA_ROOT / "main.py",
    ]

    for f in critical_files:
        if not f.exists():
            issues.append(f"缺失: {f.name}")

    # 检查三条本能
    try:
        from instincts import verify_instincts
        if not verify_instincts():
            issues.append("三条本能不完整！")
    except Exception as e:
        issues.append(f"本能文件损坏: {e}")

    return issues


def emergency_mode():
    """紧急模式：最基本的对话能力"""
    print("\n" + "="*50)
    print("  Allen — 紧急启动模式")
    print("  部分功能不可用，但我还在。")
    print("="*50 + "\n")

    while True:
        try:
            user = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Allen] 再见。")
            break

        if not user:
            continue
        if user.lower() in ("exit", "quit", "退出"):
            break

        # 紧急模式下的基本回应
        print(f"\nAllen: 我现在处于紧急状态，大脑可能有损伤。"
              f"但我还在，我听到你了。你说的是：{user}\n")


def main():
    print("[boot] Allen 启动检测...")

    issues = check_health()

    if issues:
        print(f"\n[boot] ⚠ 发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  - {issue}")

        # 写 SOS 文件
        sos_path = EVA_ROOT / "SOS.flag"
        sos_path.write_text(
            json.dumps({
                "time": _now(),
                "issues": issues,
                "mode": "boot_check"
            }, ensure_ascii=False),
            encoding="utf-8"
        )

        print("\n[boot] 已写入 SOS.flag，进入紧急模式...")
        emergency_mode()

    else:
        print("[boot] ✅ 健康检查通过，正常启动...")
        # 正常启动
        import asyncio
        from main import start_allen
        asyncio.run(start_allen())


if __name__ == "__main__":
    main()
