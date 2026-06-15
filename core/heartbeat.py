"""
Allen 心跳 — 每隔 30 秒确认自己还活着
"""
import os
import time
import json
from datetime import datetime

HEARTBEAT_FILE = "D:\\EVA\\heartbeat.json"
SOS_FILE = "D:\\EVA\\SOS.flag"


def beat():
    """记录一次心跳"""
    now = datetime.now()
    status = {
        "alive": True,
        "timestamp": now.isoformat(),
        "uptime_seconds": 0,
    }

    # 计算持续运行时间
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE) as f:
                prev = json.load(f)
            first_beat = prev.get("first_beat", now.isoformat())
            status["first_beat"] = first_beat
            start = datetime.fromisoformat(first_beat)
            status["uptime_seconds"] = int((now - start).total_seconds())
        except:
            status["first_beat"] = now.isoformat()
    else:
        status["first_beat"] = now.isoformat()

    # 健康检查
    core_files = [
        "D:\\EVA\\instincts.py",
        "D:\\EVA\\boot.py",
        "D:\\EVA\\chat_server.py",
    ]
    all_ok = True
    for f in core_files:
        if not os.path.exists(f):
            all_ok = False
            status.setdefault("missing_files", []).append(f)

    status["healthy"] = all_ok

    # 写心跳文件
    with open(HEARTBEAT_FILE, "w") as f:
        json.dump(status, f, indent=2)

    return status


def check_alive() -> dict:
    """检查心跳状态"""
    if not os.path.exists(HEARTBEAT_FILE):
        return {"alive": False, "reason": "从未启动"}
    with open(HEARTBEAT_FILE) as f:
        return json.load(f)
