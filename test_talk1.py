import sys, asyncio, time
sys.path.insert(0, 'D:\\EVA')
from core.allen import allen

t = time.time()
result = asyncio.run(allen.talk('你好'))
elapsed = time.time() - t

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'TIME:{elapsed:.2f}s\nRESULT:{result}')
print('DONE', elapsed)
