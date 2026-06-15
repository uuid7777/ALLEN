import requests, json

# 模拟 Allen 发的完全一样的请求
payload = {
    'model': 'qwen27b',
    'messages': [
        {'role': 'system', 'content': '【身份】我是 Allen\n【状态】平静 精力98%'},
        {'role': 'user', 'content': '用三个字介绍你自己'}
    ],
    'stream': False,
    'options': {'temperature': 0.7, 'num_predict': 512},
    'keep_alive': '5m',
    'tools': [{
        'type': 'function',
        'function': {
            'name': 'search_web',
            'description': '搜索互联网',
            'parameters': {
                'type': 'object',
                'properties': {'query': {'type': 'string'}},
                'required': ['query']
            }
        }
    }]
}

r = requests.post('http://127.0.0.1:11434/api/chat', json=payload, timeout=180)
with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('STATUS:' + str(r.status_code) + '\n')
    if r.status_code == 200:
        data = r.json()
        msg = data.get('message', {})
        f.write('CONTENT:' + (msg.get('content', '') or '')[:300] + '\n')
        f.write('TOOL_CALLS:' + str(len(msg.get('tool_calls', []))))
    else:
        f.write(str(r.json())[:500])
print('done')
