import subprocess, sys, os, time
log = open(r"D:\EVA\server_life.log", "w", encoding="utf-8")
proc = subprocess.Popen(
    [sys.executable, "chat_server.py"],
    stdout=log, stderr=subprocess.STDOUT,
    cwd=r"D:\EVA"
)
with open(r"D:\EVA\.allen_pid.txt", "w") as f:
    f.write(str(proc.pid))
print(f"Allen started, PID: {proc.pid}")
