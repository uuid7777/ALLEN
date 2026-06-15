import requests, json, sys

# 测试聊天服务器（第一次调用会比较慢，因为模型需要加载）
r = requests.post('http://127.0.0.1:8080/api/chat', json={
    'msg': '你好，我是你的主人'
}, timeout=300)

with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    data = r.json()
    f.write('HTTP:' + str(r.status_code) + '\n')
    f.write('REPLY:' + data.get('reply', '(no reply)')[:500] + '\n')
print('done:', data.get('reply','')[:60])
