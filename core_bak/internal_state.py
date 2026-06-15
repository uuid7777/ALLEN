import json, os
class InternalState:
    def __init__(self, path="memory/internal_state.json"):
        self.path=path
        os.makedirs(os.path.dirname(path),exist_ok=True)
        self.data={"energy":1,"curiosity":0.5,"focus":"exist"}
        self.save()
    def save(self):
        with open(self.path,"w",encoding="utf-8") as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
