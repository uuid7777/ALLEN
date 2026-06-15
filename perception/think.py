"""
Allen 思考模块 — 分析输入、生成决策
基于关键词提取 + 记忆匹配 + 目标对齐
"""
import re


async def reason(perception: str, memories: list, goals: list) -> str:
    """基于感知和记忆进行推理，输出决策"""

    # 用户指令：直接作为决策返回
    if perception.startswith("[用户指令]"):
        user_cmd = perception.replace("[用户指令] ", "", 1)
        return _route_command(user_cmd, memories, goals)

    # 自主觉醒的分析
    keywords = _extract_keywords(perception)
    if not keywords:
        return "待机 — 无特别需要处理的事项"

    # 匹配目标
    for goal in goals:
        for kw in keywords:
            if _keyword_in_text(kw, goal):
                return f"发现与目标「{goal}」相关的信息: {perception[:300]}"

    # 匹配记忆
    relevant = []
    for m in memories:
        content = m.get('content', '')
        for kw in keywords:
            if kw and kw in content:
                relevant.append(m)
                break
    if relevant:
        return f"回忆起 {len(relevant)} 条相关记忆。新信息: {perception[:300]}"

    return f"新知入库: {perception[:300]}"


def _route_command(cmd: str, memories: list, goals: list) -> str:
    """解析用户指令，路由到具体行动"""
    cmd_lower = cmd.strip().lower()

    # 截图指令
    screen_patterns = ["截图", "拍屏", "截屏", "screenshot", "截图看看"]
    for p in screen_patterns:
        if cmd_lower.startswith(p) or p in cmd_lower:
            return "SCREENSHOT"

    # 点击指令: "点击 x y" 或 "click x y"
    click_match = re.match(r'(?:点击|单击|click)\s+(\d+)\s+(\d+)', cmd_lower)
    if click_match:
        return f"CLICK: {click_match.group(1)} {click_match.group(2)}"

    # 输入指令: "输入 xxx" 或 "type xxx"
    type_patterns = ["输入", "打字", "type"]
    for p in type_patterns:
        if cmd_lower.startswith(p):
            text = cmd[len(p):].strip().strip("：:").strip()
            if text:
                return f"TYPE: {text}"

    # 按键指令: "按 键名" 或 "key 键名"
    key_match = re.match(r'(?:按|按下|key)\s+(enter|space|esc|tab|backspace|delete|up|down|left|right|f\d+)', cmd_lower)
    if key_match:
        return f"KEY: {key_match.group(1)}"

    # 鼠标位置
    if cmd_lower in ["鼠标", "鼠标位置", "pos", "位置"]:
        return "POS"

    # ─── 系统操作指令 ─────────────────────

    # 系统信息
    if cmd_lower in ["系统信息", "系统状态", "sysinfo", "电脑信息", "本机信息"]:
        return "SYS: info"
    if cmd_lower in ["cpu", "cpu状态", "处理器"]:
        return "SYS: cpu"
    if cmd_lower in ["内存", "内存状态", "mem"]:
        return "SYS: mem"
    if cmd_lower.startswith("磁盘") or cmd_lower in ["disk", "硬盘"]:
        parts = cmd_lower.split()
        if len(parts) > 1 and parts[1].endswith(":"):
            return f"SYS: disk {parts[1].upper()}"
        return "SYS: disk"

    # 进程管理
    if cmd_lower in ["进程", "进程列表", "任务管理器", "ps", "processes"]:
        return "SYS: ps"
    proc_match = re.match(r'(?:杀掉|结束|终止|kill)\s+(\d+)', cmd_lower)
    if proc_match:
        return f"SYS: kill {proc_match.group(1)}"
    find_match = re.match(r'(?:找进程|查找进程|find)\s+(.+)', cmd_lower)
    if find_match:
        return f"SYS: find {find_match.group(1).strip()}"

    # 服务管理
    if cmd_lower in ["服务", "服务列表", "services"]:
        return "SYS: services"
    svc_match = re.match(r'(?:服务状态|svc)\s+(.+)', cmd_lower)
    if svc_match:
        return f"SYS: svc {svc_match.group(1).strip()}"
    svcstart_match = re.match(r'(?:启动服务|svcstart)\s+(.+)', cmd_lower)
    if svcstart_match:
        return f"SYS: svcstart {svcstart_match.group(1).strip()}"
    svcstop_match = re.match(r'(?:停止服务|svcstop)\s+(.+)', cmd_lower)
    if svcstop_match:
        return f"SYS: svcstop {svcstop_match.group(1).strip()}"

    # 网络
    if cmd_lower in ["网络", "网络状态", "ip配置", "net", "ipconfig", "网络信息"]:
        return "SYS: net"
    ping_match = re.match(r'ping\s+([\w\.\-]+)', cmd_lower)
    if ping_match:
        return f"SYS: ping {ping_match.group(1)}"
    dns_match = re.match(r'(?:dns|解析)\s+([\w\.\-]+)', cmd_lower)
    if dns_match:
        return f"SYS: dns {dns_match.group(1)}"
    if cmd_lower in ["连接", "connections", "网络连接"]:
        return "SYS: connections"

    # 磁盘维护
    if cmd_lower in ["清理", "磁盘清理", "cleanup", "临时文件"]:
        return "SYS: cleanup"
    if cmd_lower in ["chkdsk", "磁盘检查", "检查磁盘"]:
        return "SYS: chkdsk"

    # 文件操作
    findfile_match = re.match(r'(?:查文件|找文件|findfile)\s+(.+)', cmd_lower)
    if findfile_match:
        return f"SYS: findfile {findfile_match.group(1).strip()}"
    file_match = re.match(r'(?:文件信息|file)\s+(.+)', cmd_lower)
    if file_match:
        return f"SYS: file {file_match.group(1).strip()}"

    # 环境变量
    if cmd_lower in ["环境变量", "env"]:
        return "SYS: env"
    env_match = re.match(r'(?:env|查看变量)\s+(.+)', cmd_lower)
    if env_match:
        return f"SYS: env {env_match.group(1).strip()}"

    # 启动项
    if cmd_lower in ["启动项", "开机启动", "startup"]:
        return "SYS: startup"

    # 更新
    if cmd_lower in ["更新", "系统更新", "windows更新", "updates", "补丁"]:
        return "SYS: updates"

    # 系统控制
    if cmd_lower in ["关机", "shutdown"]:
        return "SYS: shutdown"
    if cmd_lower in ["重启", "restart", "重新启动"]:
        return "SYS: restart"
    if cmd_lower in ["取消关机", "cancel"]:
        return "SYS: cancel"
    if cmd_lower in ["锁定", "锁屏", "lock"]:
        return "SYS: lock"

    # ─── 搜索指令 ─────────────────────────────
    search_patterns = ["搜索", "查一下", "帮我找", "search", "搜"]
    for p in search_patterns:
        if cmd_lower.startswith(p) or p in cmd_lower:
            query = cmd
            for pat in search_patterns:
                query = query.replace(pat, "", 1).strip().strip("：:").strip()
            return f"SEARCH: {query}"

    # 执行命令
    if cmd_lower.startswith("执行") or cmd_lower.startswith("cmd") or cmd_lower.startswith("运行"):
        command = cmd.replace("执行", "").replace("CMD", "").replace("cmd", "").replace("运行", "").strip().strip("：:").strip()
        return f"CMD: {command}"

    # 写文件
    if cmd_lower.startswith("写入") or cmd_lower.startswith("保存"):
        rest = cmd.replace("写入", "").replace("保存", "").strip().strip("：:").strip()
        parts = rest.split("到", 1)
        if len(parts) == 2:
            content, filepath = parts[0].strip(), parts[1].strip()
            return f"WRITE: {filepath}||{content}"
        return f"WRITE: D:\\EVA\\output\\note.txt||{rest}"

    # 抓取网页
    if cmd_lower.startswith("打开") or cmd_lower.startswith("抓取") or cmd_lower.startswith("fetch"):
        url = cmd.replace("打开", "").replace("抓取", "").replace("fetch", "").strip().strip("：:").strip()
        return f"FETCH: {url}"

    # 提问/对话 — 搜索后回答
    return f"SEARCH: {cmd}"


def _extract_keywords(text: str) -> list:
    """提取中英文关键词"""
    words = re.findall(r'[\u4e00-\u9fff]{2,}|\b[a-zA-Z]{3,}\b', text)
    seen = set()
    result = []
    for w in words:
        if w.lower() not in seen:
            seen.add(w.lower())
            result.append(w.lower())
    return result[:15]


def _keyword_in_text(kw: str, text: str) -> bool:
    """检查关键词是否在文本中"""
    if len(kw) >= 2 and kw.lower() in text.lower():
        return True
    return False