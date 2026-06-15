import sys, time
sys.path.insert(0, 'D:\\EVA')
print('START')
t = time.time()
from core.allen import allen
print('IMPORT DONE:', time.time() - t)
with open('D:\\EVA\\_result.txt', 'w', encoding='utf-8') as f:
    f.write('OK:' + str(time.time() - t))
