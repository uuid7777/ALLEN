import sys, asyncio
sys.path.insert(0, 'D:\\EVA')

# 先导入
from core.allen import allen

# 测试简单对话
result1 = asyncio.run(allen.talk('你好'))
print('SIMPLE:', result1)

# 测试 LLM 对话
result2 = asyncio.run(allen.talk('用一句话说说你是什么'))
print('LLM:', result2[:200])

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write('SIMPLE:' + result1 + '\n')
    f.write('LLM:' + result2[:500] + '\n')
print('ALL DONE')
