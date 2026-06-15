"""
Allen 行动模块 — 执行决策字符串
支持: SEARCH / CMD / WRITE / FETCH / SCREENSHOT / CLICK / TYPE / KEY / SYS / 默认
CMD 只允许只读安全命令，写操作一律拦截
"""
import subprocess
import requests
import re
from pathlib import Path


# ─── 安全命令白名单 ─────────────────
# 只允许这些前缀的命令，其余一律拒绝
SAFE_CMD_PREFIXES = {
    # 文件浏览（只读）
    "dir ", "tree ", "type ", "find ", "findstr ", "more ",
    # 网络诊断
    "ping ", "tracert ", "pathping ", "nslookup ", "netstat ", "route print",
    # 系统信息（只读）
    "ipconfig", "systeminfo", "ver", "whoami", "hostname",
    "tasklist", "chcp", "vol", "date /t", "time /t",
    # 环境变量（只读）
    "echo ", "set ",
}

# ─── 禁止关键词（即使出现在白名单命令的参数中也拦截） ─────
DANGEROUS_KEYWORDS = [
    "powershell", "pwsh", "cmd.exe", "cscript", "wscript", "mshta",
    "del ", "rd ", "rmdir ", "rm ",
    "format", "diskpart",
    "reg ", "regedit",
    "shutdown", "restart", "reboot",
    "curl ", "wget ", "bitsadmin", "certutil",
    "attrib", "icacls", "cacls", "takeown",
    "bcdedit", "vssadmin", "sfc ", "chkdsk", "bootrec",
    "schtasks", "sc ", "net user", "net localgroup",
    "wevtutil", "wmic", "wbadmin",
]


def is_safe_command(cmd: str) -> tuple:
    """
    检查命令是否安全。
    返回: (safe: bool, reason: str)
    白名单制——不在白名单里的命令一律拒绝。
    """
    cmd_stripped = cmd.strip()
    cmd_lower = cmd_stripped.lower()

    # 1. 禁止命令链符号
    chain_patterns = [r'\|', r'>', r'<', r'&&', r'\|\|', r';']
    for pat in chain_patterns:
        if re.search(pat, cmd_stripped):
            return (False, f"禁止使用管道/重定向/命令链符号")

    # 2. 检查是否在白名单前缀中
    allowed = False
    for prefix in SAFE_CMD_PREFIXES:
        if cmd_lower.startswith(prefix):
            allowed = True
            break
    if not allowed:
        return (False, "命令不在安全白名单中，已拦截（只允许文件浏览/网络诊断/系统信息）")

    # 3. 双重检查——命令中是否含有危险关键词
    #    比如 "dir | del" 的管道已被拦截，但 "dir C:\ && del" 也要拦
    for kw in DANGEROUS_KEYWORDS:
        if kw in cmd_lower:
            return (False, f"命令包含危险操作「{kw.strip()}」，已拦截")

    return (True, "")


async def perform(decision: str) -> str:
    """执行决策，返回结果"""

    decision_stripped = decision.strip()

    # 网页搜索
    if decision_stripped.startswith("SEARCH:") or decision_stripped.startswith("SEARCH："):
        query = decision_stripped.replace("SEARCH:", "").replace("SEARCH：", "").strip()
        try:
            from perception.web import search
            result = await search(query)
            return f"[NET]搜索结果:\n{result}"
        except Exception as e:
            return f"搜索失败: {e}"

    # 执行系统命令（仅允许安全只读命令）
    if decision_stripped.startswith("CMD:") or decision_stripped.startswith("CMD："):
        cmd = decision_stripped.replace("CMD:", "").replace("CMD：", "").strip()
        # 安全检查
        safe, reason = is_safe_command(cmd)
        if not safe:
            return f"[BLOCKED] {reason}: {cmd[:100]}"
        try:
            output = subprocess.check_output(cmd, shell=True, text=True, timeout=30, stderr=subprocess.STDOUT)
            return f"[OK]命令执行成功:\n{output[:1500]}"
        except subprocess.TimeoutExpired:
            return "[WAIT]命令超时（30秒）"
        except Exception as e:
            return f"[FAIL]命令执行失败: {e}"

    # 抓取网页
    if decision_stripped.startswith("FETCH:") or decision_stripped.startswith("FETCH："):
        url = decision_stripped.replace("FETCH:", "").replace("FETCH：", "").strip()
        try:
            from perception.web import fetch_url
            content = await fetch_url(url)
            return f"[WEB]网页内容:\n{content}"
        except Exception as e:
            return f"抓取失败: {e}"

    # 写文件
    if decision_stripped.startswith("WRITE:") or decision_stripped.startswith("WRITE："):
        rest = decision_stripped.replace("WRITE:", "").replace("WRITE：", "").strip()
        parts = rest.split("||", 1)
        if len(parts) == 2:
            filepath, content = parts[0].strip(), parts[1].strip()
        else:
            filepath = "D:\\EVA\\output\\note.txt"
            content = rest
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"[OK]文件已写入: {filepath} ({len(content)} 字符)"
        except Exception as e:
            return f"[FAIL]写文件失败: {e}"

    # HTTP 请求
    if decision_stripped.startswith("GET:") or decision_stripped.startswith("POST:"):
        method = decision_stripped.split(":", 1)[0]
        url = decision_stripped.split(":", 1)[1].strip()
        try:
            if method == "GET":
                resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            else:
                resp = requests.post(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            return f"HTTP {method} {url} → {resp.status_code} ({len(resp.text)} bytes)\n{resp.text[:800]}"
        except Exception as e:
            return f"HTTP 请求失败: {e}"

    # ─── GUI / 屏幕操作 ──────────────────────

    # 截图
    if decision_stripped.startswith("SCREENSHOT"):
        try:
            from perception.screen import screenshot
            return await screenshot()
        except Exception as e:
            return f"[FAIL]截图失败: {e}"

    # 点击
    if decision_stripped.startswith("CLICK"):
        parts = decision_stripped.replace("CLICK:", "").replace("CLICK ", "").strip().split()
        try:
            from perception.screen import click
            x, y = int(parts[0]), int(parts[1])
            btn = parts[2] if len(parts) > 2 else "left"
            return await click(x, y, btn)
        except Exception as e:
            return f"[FAIL]点击失败: {e}"

    # 输入文字
    if decision_stripped.startswith("TYPE:"):
        text = decision_stripped.replace("TYPE:", "").replace("TYPE：", "").strip()
        try:
            from perception.screen import type_text
            return await type_text(text)
        except Exception as e:
            return f"[FAIL]输入失败: {e}"

    # 按键
    if decision_stripped.startswith("KEY:"):
        key = decision_stripped.replace("KEY:", "").replace("KEY：", "").strip()
        try:
            from perception.screen import press_key
            return await press_key(key)
        except Exception as e:
            return f"[FAIL]按键失败: {e}"

    # 屏幕信息
    if decision_stripped.startswith("SCREEN") or decision_stripped.startswith("POS"):
        try:
            from perception.screen import screen_info
            return await screen_info()
        except Exception as e:
            return f"[FAIL]屏幕信息获取失败: {e}"

    # ─── 系统操作 ─────────────────────────

    if decision_stripped.startswith("SYS:"):
        cmd = decision_stripped.replace("SYS:", "").replace("SYS：", "").strip()
        try:
            from action.system import (
                sysinfo, cpu_status, mem_status, disk_status,
                list_processes, kill_process, find_process,
                network_info, ping, dns_check,
                disk_cleanup, file_info,
                env_var, startup_items, windows_update_status,
                shutdown, restart, cancel_shutdown, lock_screen,
            )
            # 路由到具体函数
            if cmd == "info" or cmd == "sysinfo":
                return await sysinfo()
            elif cmd == "cpu":
                return await cpu_status()
            elif cmd == "mem" or cmd == "memory":
                return await mem_status()
            elif cmd.startswith("disk "):
                parts = cmd.split(" ", 1)
                return await disk_status(parts[1] if len(parts) > 1 else "C:\\")
            elif cmd == "disk":
                return await disk_status()
            elif cmd == "ps" or cmd == "processes":
                return await list_processes()
            elif cmd.startswith("kill "):
                return await kill_process(int(cmd.split(" ")[1]))
            elif cmd.startswith("find "):
                return await find_process(cmd.split(" ", 1)[1])
            elif cmd == "net" or cmd == "network":
                return await network_info()
            elif cmd.startswith("ping "):
                return await ping(cmd.split(" ", 1)[1])
            elif cmd.startswith("dns "):
                return await dns_check(cmd.split(" ", 1)[1])
            elif cmd == "cleanup":
                return await disk_cleanup()
            elif cmd.startswith("file "):
                return await file_info(cmd.split(" ", 1)[1])
            elif cmd == "env":
                return await env_var()
            elif cmd.startswith("env "):
                return await env_var(cmd.split(" ", 1)[1])
            elif cmd == "startup":
                return await startup_items()
            elif cmd == "updates":
                return await windows_update_status()
            elif cmd == "shutdown":
                return await shutdown()
            elif cmd == "restart":
                return await restart()
            elif cmd == "cancel":
                return await cancel_shutdown()
            elif cmd == "lock":
                return await lock_screen()
            else:
                return f"[SYS] 未知系统指令: {cmd}。可用: info, cpu, mem, disk, ps, kill, find, net, ping, dns, cleanup, file, env, startup, updates, lock, shutdown, restart, cancel"
        except ImportError as e:
            return f"[FAIL] 系统模块未就绪: {e}"

    # ─── 默认 ────────────────────────────────
    return f"[INFO]Allen 记录: {decision_stripped[:500]}"