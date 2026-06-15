import requests, json

# 完全模拟 Allen 的调用
payload = {
    'model': 'qwen27b',
    'messages': [
        {'role': 'system', 'content': '【身份】我是 Allen\n【状态】平静'},
        {'role': 'user', 'content': '用一句话说说你是什么'}
    ],
    'stream': False,
    'options': {'temperature': 0.7, 'num_predict': 512},
    'keep_alive': '5m'
}

r = requests.post('http://127.0.0.1:11434/api/chat', json=payload, timeout=180)
with open('D:\\EVA\\_m.txt', 'w', encoding='utf-8') as f:
    f.write(str(r.status_code) + '\n')
    if r.status_code == 200:
        f.write(r.json().get('message',{}).get('content','')[:500])
    else:
        f.write(r.text[:500])
print('done', r.status_code)
