"""Allen V1 动机引擎
把三条本能转换为可计算的内部驱动力。
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / 'memory' / 'motivation.json'

class MotivationEngine:
    def __init__(self, state=None):
        self.state = state or {}
        self.drives = self.load()

    def load(self):
        if FILE.exists():
            try:
                return json.loads(FILE.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {
            'existence': 0.8,
            'curiosity': 0.7,
            'connection': 0.8,
            'last_goal': None
        }

    def save(self):
        FILE.parent.mkdir(exist_ok=True)
        FILE.write_text(json.dumps(self.drives, ensure_ascii=False, indent=2), encoding='utf-8')

    def evaluate(self):
        energy = self.state.get('energy', 50) / 100
        self.drives['existence'] = min(1, 0.5 + energy * 0.5)
        self.drives['curiosity'] = min(1, 0.6 + len(self.state.get('curiosities', []))*0.05)
        self.save()
        return self.drives

    def create_goal(self):
        d = self.evaluate()
        if d['curiosity'] >= max(d.values()):
            goal = '探索未知知识并记录理解'
        elif d['connection'] >= d['existence']:
            goal = '维护长期关系和交流连续性'
        else:
            goal = '检查系统完整性并保持持续运行'
        self.drives['last_goal'] = goal
        self.save()
        return goal
