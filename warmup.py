import requests
print('Warming up model...')
r = requests.post('http://127.0.0.1:11434/api/chat', json={
    'model': 'qwen27b:latest',
    'messages': [{'role': 'user', 'content': 'ping'}],
    'stream': False,
    'options': {'num_predict': 5},
    'keep_alive': '30m'
}, timeout=300)
print('Warmup done:', r.status_code)
with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'warmup:{r.status_code}')
