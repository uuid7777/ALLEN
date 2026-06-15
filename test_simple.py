import requests, json

# 最简单的请求，没有 keep_alive
r = requests.post('http://127.0.0.1:11434/api/chat', json={
    'model': 'qwen27b',
    'messages': [{'role': 'user', 'content': 'hi'}],
    'stream': False,
    'options': {'num_predict': 50}
}, timeout=120)
with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('STATUS:' + str(r.status_code) + '\n')
    if r.status_code == 200:
        data = r.json()
        detail = data.get('message', {}).get('content', '')[:200]
        f.write('CONTENT:' + detail)
        f.write('\nDURATION:' + str(data.get('total_duration', 0) // 1000000) + 'ms')
    else:
        f.write(str(r.json())[:500])
print('done')
