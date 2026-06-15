import requests, json
# 先测试 Ollama 是否还在线
r = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)
print('tags:', r.status_code, json.dumps(r.json(), ensure_ascii=False)[:200])

# 再测试 warm 的模型
r2 = requests.post('http://127.0.0.1:11434/api/chat', json={
    'model': 'qwen27b:latest',
    'messages': [{'role': 'user', 'content': 'hi'}],
    'stream': False,
    'options': {'num_predict': 10}
}, timeout=120)
print('chat:', r2.status_code)
if r2.status_code == 200:
    print(r2.json().get('message',{}).get('content','')[:200])
else:
    print(r2.text[:300])

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'{r2.status_code}\n{r2.text[:500]}')
