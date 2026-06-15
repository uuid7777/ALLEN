"""测试: 直接启动 chat_server 并发送请求"""
import sys, subprocess, time, requests, os, signal

# 启动 server
proc = subprocess.Popen(
    [sys.executable, 'D:\\EVA\\chat_server.py'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    cwd='D:\\EVA',
    creationflags=subprocess.CREATE_NO_WINDOW,
)
time.sleep(2)

# 先读取启动输出
startup = b''
while True:
    try:
        line = proc.stdout.readline()
        if line:
            startup += line
        else:
            break
    except:
        break
    if b'PID' in line:
        break

# 发送请求
try:
    r = requests.post('http://127.0.0.1:8080/api/chat',
        json={'msg': '用一句话说说你是什么'}, timeout=120)
    reply = r.json().get('reply', '?')[:200]
except Exception as e:
    reply = f'HTTP ERROR: {e}'

# 再读剩余的 server 输出
time.sleep(0.5)
rest = b''
while True:
    try:
        line = proc.stdout.readline()
        if line:
            rest += line
        else:
            break
    except:
        break

proc.terminate()
proc.wait(timeout=3)

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'STARTUP:\n{startup.decode("utf-8", errors="replace")}\n')
    f.write(f'AFTER REQUEST:\n{rest.decode("utf-8", errors="replace")}\n')
    f.write(f'REPLY:\n{reply}\n')
print('DONE')
