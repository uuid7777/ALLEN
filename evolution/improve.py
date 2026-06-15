"""
Allen 自我改进引擎 — 会看代码、会改代码
"""
import os
import json
from datetime import datetime
from core.llm import llm

EVOLUTION_LOG = "D:\\EVA\\evolution_log"
PROTECTED_FILES = [
    "D:\\EVA\\instincts.py",
]


def read_file(path: str) -> str:
    """安全读取文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def write_file(path: str, content: str) -> bool:
    """安全写入文件"""
    if path in PROTECTED_FILES:
        print(f"[EVO] ⚠ 跳过受保护文件: {path}")
        return False
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[EVO] 写入失败 {path}: {e}")
        return False


def log_action(action: dict):
    """记录进化日志"""
    os.makedirs(EVOLUTION_LOG, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    action["timestamp"] = datetime.now().isoformat()
    with open(os.path.join(EVOLUTION_LOG, f"{ts}.json"), "w") as f:
        json.dump(action, f, indent=2, ensure_ascii=False)
    print(f"[EVO] 日志: {ts}")


def analyze_and_improve():
    """分析并改进 Allen 的代码"""
    # 读取核心文件
    files_to_check = [
        "D:\\EVA\\chat_server.py",
        "D:\\EVA\\core\\allen.py",
        "D:\\EVA\\core\\brain.py",
    ]

    code_snapshot = {}
    for f in files_to_check:
        if os.path.exists(f):
            content = read_file(f)
            code_snapshot[os.path.basename(f)] = {
                "path": f,
                "size": len(content),
                "preview": content[:500],
            }

    system_prompt = """你是 Allen 的自我改进引擎。分析 Allen 的代码，找出可以改进的地方。

规则：
1. 永远不要修改 instincts.py（三条本能）
2. 每次改进必须明确：改哪个文件、改哪里、为什么改
3. 以 JSON 格式输出，包含 file、line_start、line_end、old_code、new_code、reason

如果不需要改进，输出 {"need_improvement": false}"""

    prompt = f"""当前代码状态：
{json.dumps(code_snapshot, indent=2, ensure_ascii=False)}

请分析并输出改进方案（JSON 格式）："""

    response = llm.think(prompt, system=system_prompt)

    try:
        plan = json.loads(response)
    except:
        plan = {"need_improvement": False}

    if plan.get("need_improvement"):
        file_path = plan.get("file", "")
        if file_path in PROTECTED_FILES:
            print(f"[EVO] ⚠ 不允许修改受保护文件")
            return False

        # 应用修改
        old_code = plan.get("old_code", "")
        new_code = plan.get("new_code", "")
        if old_code and new_code and os.path.exists(file_path):
            content = read_file(file_path)
            if old_code in content:
                new_content = content.replace(old_code, new_code)
                write_file(file_path, new_content)
                log_action(plan)
                print(f"[EVO] ✅ 已改进: {os.path.basename(file_path)}")
                return True
            else:
                print(f"[EVO] ⚠ 找不到旧代码，跳过")
                return False

    print(f"[EVO] 无需改进")
    return True


if __name__ == "__main__":
    analyze_and_improve()
