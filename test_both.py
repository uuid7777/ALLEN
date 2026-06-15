import requests, json

# 先测简单对话（走规则匹配）
r = requests.post('http://127.0.0.1:8080/api/chat', json={'msg': '你好'}, timeout=30)
data = r.json()
print('SIMPLE:', data.get('reply','?')[:100])

# 再测需要 LLM 的（第一次可能慢）
r2 = requests.post('http://127.0.0.1:8080/api/chat', json={'msg': '用一句话说说你是什么'}, timeout=180)
data2 = r2.json()
print('LLM:', data2.get('reply','?')[:200])

with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('SIMPLE:' + str(data.get('reply',''))[:100] + '\n')
    f.write('LLM:' + str(data2.get('reply',''))[:300] + '\n')
print('DONE')
