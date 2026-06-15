"""每日反思与成长记录"""
import json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent.parent
FILE=ROOT/'memory'/'reflection.json'

class Reflection:
    def write(self, text):
        data=[]
        if FILE.exists():
            try:data=json.loads(FILE.read_text(encoding='utf-8'))
            except:pass
        data.append({'time':datetime.now().isoformat(),'reflection':text})
        FILE.parent.mkdir(exist_ok=True)
        FILE.write_text(json.dumps(data[-100:],ensure_ascii=False,indent=2),encoding='utf-8')
