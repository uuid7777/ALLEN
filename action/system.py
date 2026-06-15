"""
Allen 系统操作模块 — 管理/配置/修复 Windows 系统
纯 Python + subprocess，零外部依赖
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


async def sysinfo():
    """获取完整的系统信息"""
    if HAS_PSUTIL:
        cpu_count = psutil.cpu_count(logical=True)
        cpu_phys = psutil.cpu_count(logical=False)
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        from datetime import datetime
        boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"[SYS] 主机名: {platform.node()}\n"
            f"[SYS] 系统: {platform.system()} {platform.release()}\n"
            f"[SYS] 架构: {platform.machine()}\n"
            f"[SYS] 处理器: {cpu_phys} 物理核 / {cpu_count} 逻辑核 ({cpu_percent}%)\n"
            f"[SYS] 内存: {mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB ({mem.percent}%)\n"
            f"[SYS] C盘: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)\n"
            f"[SYS] 启动: {boot}\n"
            f"[SYS] 进程数: {len(psutil.pids())}"
        )
    return await _run_cmd("systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"")


async def cpu_status():
    if not HAS_PSUTIL:
        return "[FAIL] 需要 psutil 库"
    percent = psutil.cpu_percent(interval=1)
    freq = psutil.cpu_freq()
    freq_str = f"{freq.current:.0f}MHz" if freq else "N/A"
    cores = []
    for i, p in enumerate(psutil.cpu_percent(interval=0.5, percpu=True)):
        cores.append(f"    核{i}: {p}%")
    return f"[CPU] 使用率: {percent}%\n[CPU] 频率: {freq_str}\n" + "\n".join(cores)


async def mem_status():
    if not HAS_PSUTIL:
        return "[FAIL] 需要 psutil 库"
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return (
        f"[MEM] 总内存: {mem.total // (1024**3)}GB\n"
        f"[MEM] 已用: {mem.used // (1024**3)}GB ({mem.percent}%)\n"
        f"[MEM] 可用: {mem.available // (1024**3)}GB\n"
        f"[MEM] 交换: {swap.used // (1024**3)}GB / {swap.total // (1024**3)}GB"
    )


async def disk_status(path="C:\\"):
    if not HAS_PSUTIL:
        return "[FAIL] 需要 psutil 库"
    lines = []
    for p in psutil.disk_partitions():
        if p.fstype:
            try:
                u = psutil.disk_usage(p.mountpoint)
                lines.append(f"  {p.device} ({p.mountpoint}) [{p.fstype}] "
                             f"{u.used // (1024**3)}GB / {u.total // (1024**3)}GB ({u.percent}%)")
            except (PermissionError, OSError):
                lines.append(f"  {p.device} - 无法读取")
    return "[DISK] 磁盘:\n" + "\n".join(lines)


async def list_processes(top=20):
    if not HAS_PSUTIL:
        return await _run_cmd("tasklist /FI \"STATUS eq RUNNING\" /FO TABLE /NH")
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "status"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x.get("memory_percent", 0) or 0, reverse=True)
    lines = [f"[PROC] 进程 (前{top}):"]
    for p in procs[:top]:
        lines.append(f"  PID:{p['pid']:>6}  {p['name'][:30]:<30}  MEM:{p.get('memory_percent',0):.1f}%  [{p.get('status','')}]")
    return "\n".join(lines)


async def kill_process(pid: int):
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        proc.wait(timeout=3)
        return f"[OK] 已终止: {name} (PID {pid})"
    except psutil.NoSuchProcess:
        return f"[FAIL] 进程不存在: PID {pid}"
    except psutil.AccessDenied:
        return f"[FAIL] 权限不足: PID {pid}"
    except Exception as e:
        return f"[FAIL] {e}"


async def find_process(name: str):
    if not HAS_PSUTIL:
        return await _run_cmd(f"tasklist /FI \"IMAGENAME eq {name}*\"")
    matches = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "status"]):
        try:
            if name.lower() in p.info["name"].lower():
                matches.append(f"  PID:{p.info['pid']:>6}  {p.info['name'][:30]:<30}  MEM:{p.info.get('memory_percent',0):.1f}%  [{p.info['status']}]")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if matches:
        return f"[PROC] 找到 {len(matches)} 个 \"{name}\":\n" + "\n".join(matches)
    return f"[PROC] 未找到: {name}"


async def network_info():
    return await _run_cmd("ipconfig")


async def ping(host="8.8.8.8", count=4):
    return await _run_cmd(f"ping {host} -n {count}")


async def dns_check(domain="baidu.com"):
    return await _run_cmd(f"nslookup {domain} 2>nul")


async def disk_cleanup():
    results = []
    temp_dirs = [
        os.environ.get("TEMP", ""),
        os.environ.get("TMP", ""),
        r"C:\Windows\Temp",
    ]
    for d in temp_dirs:
        if d and os.path.exists(d):
            count = 0
            size = 0
            for root, dirs, files in os.walk(d):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        size += os.path.getsize(fp)
                        os.remove(fp)
                        count += 1
                    except (PermissionError, OSError):
                        pass
                    if count > 200:
                        break
            if count > 0:
                results.append(f"  {d}: {count} 文件, {size // 1024}KB")
    if results:
        return "[CLEAN] 清理完成:\n" + "\n".join(results)
    return "[CLEAN] 无可清理文件"


async def file_info(path: str):
    p = Path(path)
    if not p.exists():
        return f"[FAIL] 不存在: {path}"
    if p.is_file():
        size = p.stat().st_size
        from datetime import datetime
        mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return f"[FILE] {p.resolve()}\n  大小: {size:,} 字节\n  修改: {mt}"
    else:
        items = list(p.iterdir())[:30]
        dirs = [x.name + "/" for x in items if x.is_dir()]
        files = [x.name for x in items if x.is_file()]
        return (f"[DIR] {p.resolve()} ({len(dirs)} 目录, {len(files)} 文件)\n"
                f"  目录: {', '.join(dirs[:10])}\n"
                f"  文件: {', '.join(files[:10])}")


async def env_var(name=""):
    if name:
        val = os.environ.get(name, "")
        return f"[ENV] {name}={val}" if val else f"[ENV] 不存在: {name}"
    important = ["PATH", "USERNAME", "COMPUTERNAME", "OS", "PROCESSOR_ARCHITECTURE",
                 "NUMBER_OF_PROCESSORS", "APPDATA", "TEMP"]
    lines = ["[ENV] 环境变量:"]
    for k in important:
        lines.append(f"  {k}={os.environ.get(k, '')[:100]}")
    return "\n".join(lines)


async def startup_items():
    return await _run_cmd("wmic startup get caption,command")


async def windows_update_status():
    return await _run_cmd("wmic qfe get HotFixID,InstalledOn 2>nul | findstr /N .")


async def shutdown(delay=60):
    return await _run_cmd(f"shutdown /s /t {delay}")


async def restart(delay=60):
    return await _run_cmd(f"shutdown /r /t {delay}")


async def cancel_shutdown():
    return await _run_cmd("shutdown /a")


async def lock_screen():
    return await _run_cmd("rundll32.exe user32.dll,LockWorkStation")


# ─── 工具 ─────────────────────────────

async def _run_cmd(cmd: str) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, encoding="gbk", errors="replace"
        )
        out = result.stdout or result.stderr or "(无输出)"
        if len(out) > 1500:
            out = out[:1500] + f"\n...(截断 {len(out)} 字符)"
        return f"[CMD] {out.strip()}"
    except subprocess.TimeoutExpired:
        return "[WAIT] 命令超时"
    except Exception as e:
        return f"[FAIL] {e}"
