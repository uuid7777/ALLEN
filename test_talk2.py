import sys, asyncio, time
sys.path.insert(0, 'D:\\EVA')
from core.allen import allen

t = time.time()
result = asyncio.run(allen.talk('用一句话说说你是什么'))
elapsed = time.time() - t

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'TIME:{elapsed:.2f}s\nRESULT:{result[:500]}')
print('DONE', elapsed, 'RESULT:', result[:100])
