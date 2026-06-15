import requests, json
r = requests.post('http://127.0.0.1:11434/api/chat', json={
    'model': 'qwen27b',
    'messages': [{'role': 'user', 'content': '你好'}],
    'stream': False,
    'options': {'temperature': 0.7, 'num_predict': 512}
}, timeout=120)
with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('STATUS:' + str(r.status_code) + '\n')
    if r.status_code == 200:
        data = r.json()
        f.write(data.get('message', {}).get('content', '(no content)')[:300])
    else:
        f.write(str(r.json())[:500])
print('done')
