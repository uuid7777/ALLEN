import sys, os, json, asyncio, threading, time
from pathlib import Path

# 直接手动测试 Allen
sys.path.insert(0, 'D:\\EVA')
from core.allen import allen

# 测试不需要 LLM 的
r1 = asyncio.run(allen.talk('你好'))
print('SIMPLE:', r1)

# 测试需要 LLM 的
t = time.time()
r2 = asyncio.run(allen.talk('用一句话说说你是什么'))
print(f'LLM({time.time()-t:.1f}s):', r2[:200])

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'SIMPLE:{r1}\nLLM:{r2[:500]}')
