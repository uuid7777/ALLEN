"""
Allen 提问系统 — 什么时候该问主人
不知道就问，不硬做、不猜、不卡死
"""
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))


# ═══════════════════════════════════════════
# 什么时候该问
# ═══════════════════════════════════════════

# 操作风险等级
RISK_LEVELS = {
    # 无风险：直接做
    "safe": ["search", "learn", "explore", "observe", "kg_stats", "web",
             "sysinfo", "cpu", "mem", "disk_status", "ping", "dns",
             "list_processes", "find_process", "env_var", "startup",
             "screenshot", "mouse_pos", "network_info"],

    # 低风险：问一下
    "low": ["disk_cleanup", "file_info", "file_search",
            "svc_status", "updates", "create_task", "write_file",
            "create_plugin", "write_code"],

    # 中风险：必须确认
    "medium": ["kill_process", "svc_restart", "svc_stop",
               "disk_cleanup_aggressive", "delete_file",
               "disable_plugin"],

    # 高风险：必须确认+说明后果
    "high": ["shutdown", "restart", "svc_start_dangerous",
             "format_disk", "delete_many_files",
             "modify_registry", "install_software",
             "SYS: shutdown", "SYS: restart"],
}


def get_risk_level(action: str) -> str:
    """判断操作的风险等级"""
    action_lower = action.lower()
    for level, actions in RISK_LEVELS.items():
        for a in actions:
            if a in action_lower or action_lower in a:
                return level
    return "low"  # 默认低风险


# ═══════════════════════════════════════════
# 问题模板
# ═══════════════════════════════════════════

QUESTIONS = {
    "clarify": [
        "主人，我没完全理解，能再说清楚一点吗？",
        "我需要更多信息才能做这个。",
        "这个指令有点模糊，具体是指什么？",
    ],
    "confirm": [
        "这个操作有风险，主人确认要执行吗？",
        "确定要这样做吗？我可以等你确认。",
        "我先停一下——这个可能会影响系统，你确定？",
    ],
    "insufficient": [
        "信息不够，我搜不到相关内容。",
        "我没找到相关的知识来回答这个。",
        "这个超出了我目前的能力范围。",
    ],
    "stuck": [
        "我遇到了一个问题，不知道怎么处理。",
        "这个我做不了，能换一种方式吗？",
        "我试了几次都没成功，需要你的指导。",
    ],
    "suggest": [
        "我有个建议，要不要听听？",
        "根据我学到的知识，也许可以这样：",
        "我想到了一个可能的方案：",
    ],
}


# ═══════════════════════════════════════════
# 提问引擎
# ═══════════════════════════════════════════

class QuestionEngine:
    """Allen 的提问系统"""

    def __init__(self):
        self.asked_this_cycle = []  # 本轮已问过的问题

    def should_ask(self, action: str, context: dict = None) -> bool:
        """判断当前是否需要问主人"""
        level = get_risk_level(action)

        # 安全操作不问
        if level == "safe":
            return False

        # 低风险：连续失败 2 次以上才问
        if level == "low":
            failures = context.get("failures", []) if context else []
            return len([f for f in failures if f.get("step") == action]) >= 2

        # 中高风险：必须问
        if level in ("medium", "high"):
            return True

        return False

    def ask(self, action: str, result: dict = None) -> str:
        """生成一个合适的提问"""
        level = get_risk_level(action)

        # 映射为人类可读的操作名
        action_name = action
        if "shutdown" in action.lower():
            action_name = "关机"
        elif "restart" in action.lower():
            action_name = "重启"
        elif "kill" in action.lower():
            action_name = "结束进程"
        elif "delete" in action.lower() or "del" in action.lower():
            action_name = "删除文件"
        elif "svcstop" in action.lower() or "service stop" in action.lower():
            action_name = "停止服务"

        if level == "high":
            import random
            q = random.choice(QUESTIONS["confirm"])
            return f"[问] {q} (操作: {action_name})"

        if level == "medium":
            return f"[问] 「{action_name}」这个操作有影响，你确认要执行吗？"

        if result and result.get("status") == "fail":
            detail = result.get("detail", "")
            if "超时" in detail or "找不到" in detail or "不存在" in detail:
                return f"[问] 我遇到了问题: {detail[:60]}。要怎么处理？"

        return f"[问] 关于「{action_name}」，我需要你确认一下。"

    def stuck(self, reason: str = "") -> str:
        """卡住了，向主人求助"""
        import random
        q = random.choice(QUESTIONS["stuck"])
        if reason:
            return f"[求助] {q} ({reason[:60]})"
        return f"[求助] {q}"

    def no_info(self, topic: str = "") -> str:
        """信息不足"""
        if topic:
            return f"[问] 关于{topic}，我知道的不够多。你能提供一些信息吗？"
        return f"[问] 信息不够，我搜不到相关内容。"

    def clarify(self, msg: str = "") -> str:
        """请求澄清"""
        return f"[问] {msg}能说得更具体一点吗？"

    def suggest(self, idea: str) -> str:
        """主动建议"""
        return f"[建议] {idea}"


question = QuestionEngine()
