import requests, json

# 等模型加载完成
print('Sending...')

r = requests.post('http://127.0.0.1:8080/api/chat', json={
    'msg': '用一句话说说你是什么'
}, timeout=500)

data = r.json()
reply = data.get('reply', '?')

with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write(reply[:500])

print('REPLY:', reply[:200])
