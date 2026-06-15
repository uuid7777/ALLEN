import requests, json

# 不带 tools
payload = {
    'model': 'qwen27b',
    'messages': [
        {'role': 'system', 'content': '【身份】我是 Allen\n【状态】平静 精力98%'},
        {'role': 'user', 'content': '用三个字介绍你自己'}
    ],
    'stream': False,
    'options': {'temperature': 0.7, 'num_predict': 512},
    'keep_alive': '5m'
}

r = requests.post('http://127.0.0.1:11434/api/chat', json=payload, timeout=120)
with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('STATUS:' + str(r.status_code) + '\n')
    if r.status_code == 200:
        data = r.json()
        msg = data.get('message', {})
        f.write('CONTENT:' + (msg.get('content', '') or '(empty)')[:300])
    else:
        f.write(str(r.json())[:500])
print('done')
