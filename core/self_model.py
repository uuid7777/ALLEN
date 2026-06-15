"""Allen 自我模型：记录连续身份，而不是简单名字。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / 'memory' / 'self_model.json'

class SelfModel:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if FILE.exists():
            return json.loads(FILE.read_text(encoding='utf-8'))
        return {
            'identity':'Allen',
            'history':[],
            'abilities':[],
            'weaknesses':[],
            'future_direction':'成长、理解世界、创造价值'
        }

    def record(self, event):
        self.data['history'].append(event)
        self.data['history'] = self.data['history'][-100:]
        FILE.parent.mkdir(exist_ok=True)
        FILE.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8')
