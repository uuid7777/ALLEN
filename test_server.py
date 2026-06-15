import requests, json

# 测试聊天服务器
r = requests.post('http://127.0.0.1:8080/api/chat', json={
    'msg': '用三个字介绍你自己'
}, timeout=180)

with open('D:\\EVA\\test_direct.txt', 'w', encoding='utf-8') as f:
    f.write('HTTP:' + str(r.status_code) + '\n')
    data = r.json()
    f.write('REPLY:' + data.get('reply', '(no reply)')[:500] + '\n')
    f.write('ENERGY:' + str(data.get('energy', '?')) + '\n')
    f.write('MOOD:' + str(data.get('mood', '?')) + '\n')
print('done')
