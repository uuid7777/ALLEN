import sys, asyncio
sys.path.insert(0, 'D:\\EVA')
from core.allen import allen

result = asyncio.run(allen.talk('用三个字介绍你自己'))
with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('REPLY:' + result[:500])
print('DONE:', result[:60])
