import requests, json
# 直接测试 qwen27b:latest
r = requests.post('http://127.0.0.1:11434/api/chat', json={
    'model': 'qwen27b:latest',
    'messages': [{'role': 'user', 'content': 'hi'}],
    'stream': False,
    'options': {'num_predict': 10}
}, timeout=60)
with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(str(r.status_code) + '\n' + r.text[:500])
print('STATUS:', r.status_code)
